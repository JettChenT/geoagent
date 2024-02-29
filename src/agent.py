import os
import sys
from typing import Tuple, Optional, List
from enum import Enum
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, wait

from langchain.tools.render import render_text_description
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
from rich import print

from . import config, utils
from .prompting import *
from .connector.gptv import Gpt4Vision
from .connector import LMM, Message
from .tools import TOOLS, find_tool
from .context import Context, CtxState
from .react_parser import ReActSingleInputOutputParser
from .coords import Coords
from .sock import start_srv
from .subscriber import Subscriber, SIOSubscriber

if os.getenv("FUNTRACE"):
    import functiontrace
    import _functiontrace

    functiontrace.setup_dependencies()
    _functiontrace.begin_tracing("./trace")


def select_node(node: Context):
    while node and node.children:
        logging.info(f"Selecting from {len(node.children)} children at depth {node.depth}.")

        terminal_children = [child for child in node.children if child.is_terminal]
        terminal_status = [child.is_terminal for child in node.children]

        if len(terminal_children) == len(node.children):
            logging.info(f"All children are terminal at depth {node.depth}. Backtracking...")
            if node.parent:
                node.parent.children.remove(node)
            node = node.parent
            continue

        node_with_reward_1 = next((child for child in terminal_children if child.reward == 1), None)
        if node_with_reward_1:
            logging.info(f"Found terminal node with reward 1 at depth {node.depth}.")
            return node_with_reward_1

        node = max((child for child in node.children if not child.is_terminal), key=lambda child: child.uct(),
                   default=None)

        while node.is_terminal and node.reward != 1:
            node = max((child for child in node.parent.children if not child.is_terminal),
                       key=lambda child: child.uct(), default=None)
        logging.info(f"Selected node at depth {node.depth} with UCT {node.uct()}.")
    return node


def backprop(node: Context, value):
    while node:
        node.visits += 1
        if node.is_terminal:
            if node.reward == 0:
                node.value = (node.value * (node.visits - 1) + (-1)) / node.visits
            else:
                node.value = (node.value * (node.visits - 1) + value) / node.visits
        else:
            node.value = (node.value * (node.visits - 1) + value) / node.visits
        node.notify()
        node = node.parent


def collect_all_nodes(node: Context):
    nodes = [node]
    for child in node.children:
        nodes.extend(collect_all_nodes(child))
    return nodes


def print_tree(node: Context, indent: int = 0, highlight: Context = None):
    if node == highlight:
        print(f"{'  ' * indent}[red]*[/red] {node}")
    else:
        print(f"{'  ' * indent}* {node}")
    for child in node.children:
        print_tree(child, indent + 1, highlight)


class RunType(Enum):
    INTERACTIVE = 1
    PARALLEL = 2
    EVALUATE = 1


class Agent:
    DEPTH_THRESHOLD = 10
    ROLLOUT_THRESHOLD = 6
    BRANCH_CNT = 3

    def __init__(self, vllm: LMM, run_type: RunType = RunType.PARALLEL, subscriber: Optional[Subscriber] = None):
        self.vllm = vllm
        self.depth = 0
        self.output_parser = ReActSingleInputOutputParser()
        self.run_type = run_type
        self.subscriber = subscriber

    @Context.wrap_state(CtxState.Expanding)
    def expand_node(self, node: Context):
        logging.info(f"expanding node {hex(id(node))}.....")
        if node.depth >= self.DEPTH_THRESHOLD:
            node.is_terminal = True
            return
        sampled = self.vllm.prompt(node, stop=["Observation"], n=self.BRANCH_CNT)
        logging.info(f"Sampled {len(sampled)} messages")
        tasks = []
        existing = set()
        for s in sampled:
            logging.info(f"Sampled message: {s}")
            new_st = node.commit(message=s)
            try:
                parsed = self.output_parser.parse(s.message)
            except Exception as e:
                print(e)
                new_st.add_message(
                    Message(
                        f"Could not parse output: {e} \nAnalyze{node.depth}: "
                    )
                )
                continue
            if (k := str(parsed.to_json()) if isinstance(parsed, AgentFinish) else (
            parsed.tool, utils.sanitize(parsed.tool_input))) in existing:
                continue
            existing.add(k)
            new_st.transition = parsed
            logging.info(f"Parsed message: {parsed}")
            t = threading.Thread(target=self.run_observe, args=(new_st,))
            t.start()
            if self.run_type == RunType.INTERACTIVE:
                t.join()
            tasks.append(t)

        logging.info(f"Waiting for {len(tasks)} tasks to finish")
        for t in tasks:
            t.join()

    @Context.wrap_state(CtxState.Rollout)
    def rollout(self, node: Context) -> Tuple[float, Context]:
        print("-----------Rolling out----------")
        dep = 0
        rewards = [0]
        while not node.is_terminal and dep < self.ROLLOUT_THRESHOLD:
            print("Rollout depth", dep)
            print("current node", str(node))
            self.expand_node(node)
            if len(node.children) == 0:
                break
            for c in node.children:
                if c.is_terminal: return c.reward, c
            values = self.get_values(node.children)
            mx_ind = values.index(max(values))
            rewards.append(max(values))
            node = node.children[mx_ind]
            dep += 1
            if dep == self.ROLLOUT_THRESHOLD:
                rewards = [-1]
        return sum(rewards) / len(rewards), node

    @Context.wrap_state(CtxState.Evaluating)
    def evaluate_node(self, node: Context):
        node.set_state(CtxState.Evaluating)
        votes = self.get_values(node.children)
        print("setting votes...", votes)
        for i, c in enumerate(node.children):
            c.value = votes[i]
        return sum(votes) / len(votes) if votes else 0

    @Context.wrap_state(CtxState.Running)
    def run_observe(self, state: Context):
        """
        Make an observation. This mutates the state.
        :param state:
        :return:
        """
        if state.transition is None:
            state.add_message(Message(f"Could not parse output, please adjust your input. \nAnalyze{state.depth}: "))
            return
        if isinstance(state.transition, AgentFinish):
            if self.run_type != RunType.INTERACTIVE:
                state.reward = self.get_reward(state)
                return
            isok = input("Is this ok? (y/n)")
            if isok == "y":
                state.is_terminal = True
                state.reward = 1
            else:
                feedback = input("Enter feedback:")
                state.add_message(Message(f"Feedback: {feedback}\nAnalyze{state.depth}: "))
            return
        tool: BaseTool | None = find_tool(state.transition.tool)
        if tool is None:
            state.add_message(
                Message(
                    f"Could not find tool {state.transition.tool}, please adjust your input. \nAnalyze{state.depth}: "
                )
            )
            return
        try:
            tool_res = str(
                tool._run(*utils.get_args(tool, utils.sanitize(state.transition.tool_input)))
            )  # TODO: Make multi-argument parsing more robust
        except Exception as e:
            print('[red]Error[/red]: ', e)
            # ask if user would like to continue, if so, ask for potential feedback
            if self.run_type != RunType.INTERACTIVE:
                state.add_message(
                    Message(
                        f"Could not run tool {state.transition.tool}: {e}\n please adjust. \nAnalyze{state.depth}: "
                    )
                )
                return
            docontinue = input("Continue? (y/n)")
            if docontinue == "n":
                return
            feedback = input("Enter feedback if any:")
            state.add_message(
                Message(
                    f"Could not run tool {state.transition.tool}: {e}, {feedback}\n please adjust. \nAnalyze{state.depth}: "
                )
            )
            return
        if tool.return_direct:
            state.is_terminal = True
            if self.run_type == RunType.INTERACTIVE:
                isok = input("Is this ok? (y/n)")
                if isok == "y":
                    state.reward = 1
                else:
                    feedback = input("Enter feedback:")
                    tool_res += "\nFeedback: " + feedback
            else:
                state.reward = self.get_reward(state)
        state.add_message(
            Message(f"Observation{state.depth}: {tool_res}\nAnalyze{state.depth}: ")
        )
        state.set_observation(tool_res)

    @Context.wrap_state(CtxState.Evaluating)
    def get_value(self, node: Context):
        messages = node.messages
        messages.append(Message(VALUE_PROMPT))
        res = self.vllm.prompt(messages, temperature=0.1)[0]
        targ_line = res.message.splitlines()[-1]
        for i in range(10, 0, -1):
            if str(i) in targ_line:
                logging.info(f"Found value {i} in {targ_line}")
                node.set_auxiliary("value", i / 10)
                return i / 10
        return -1

    def get_values(self, nodes: List[Context]):
        messages = nodes[0].parent.messages
        for i, node in enumerate(nodes):
            messages.append(Message(f"Begin Branch {i}: "))
            messages += node.cur_messages
            messages.append(Message(f"End Branch {i}"))

        messages.append(Message(MULTI_EVALUATION_PROMPT.format(n=len(nodes))))
        messages.append(Message(f"Now, begin your evaluation for each of the {len(nodes)} branches."))
        for n in nodes:
            n.set_state(CtxState.Evaluating)
        res = self.vllm.prompt(messages, temperature=0.1)[0]
        targ_lines = res.message.splitlines()[-len(nodes):]
        print('targ lines: ', targ_lines)
        values = []
        for i in range(len(nodes)):
            nodes[i].set_state(CtxState.Normal)
            for j in range(10, 0, -1):
                if str(j) in targ_lines[i].split(":")[-1]:
                    logging.info(f"Found value {j} in {targ_lines[i]}")
                    nodes[i].set_auxiliary("value", j / 10)
                    values.append(j / 10)
                    break
            else:
                nodes[i].set_auxiliary("value", 0)
                values.append(0)
        return values

    @Context.wrap_state(CtxState.Evaluating)
    def get_reward(self, node: Context):
        # TODO: augment the reward prompt with coordinate data etc.
        messages = node.messages
        messages.append(Message(REWARD_PROMPT))
        res = self.vllm.prompt(messages, temperature=0.1)[0]
        targ_line = res.message.splitlines()[-1]
        for i in range(10, 0, -1):
            if str(i) in targ_line:
                logging.info(f"Found value {i} in {targ_line}")
                node.set_auxiliary("reward", i / 10)
                return i / 10
        return 0

    def lats(self, image_loc: str, additional: str = "") -> Context:
        utils.flush_run_dir()
        root = Context(tools=TOOLS, subscriber=self.subscriber)
        root.add_message(
            Message(
                INITIAL_REACT_PROMPT.format(
                    tool_names=", ".join([t.name for t in TOOLS]),
                    tools=render_text_description(TOOLS),
                    input=f"{utils.image_to_prompt(image_loc)} Where is this image located? {additional}",
                )
            )
        )
        terminals = []

        for i in range(1, self.DEPTH_THRESHOLD + 1):
            node = select_node(root)
            logging.info(f"Selected node at depth {node.depth}: {node.messages[-1]}")
            print("-----Before expansion-----")
            print_tree(root, highlight=node)
            self.expand_node(node)
            print("-----After expansion-----")
            print_tree(root)
            values = self.get_values(node.children)
            if len(values) == 0 or len(node.children) == 0:
                logging.info(f"No values found for node {node}")
                continue
            reward, terminal = self.rollout(max(enumerate(node.children), key=lambda v: values[v[0]])[1])
            terminal: Context
            terminals.append(terminal)
            if terminal.reward == 1:
                print_tree(root)
                print(f"successful solution has been found: {terminal.transition.tool_input}")
                terminal.set_state(CtxState.Success)
                return terminal
            backprop(terminal, reward)
            terminal_nodes_with_reward_1 = [node for node in collect_all_nodes(root) if
                                            node.is_terminal and node.reward == 1]
            if terminal_nodes_with_reward_1:
                return max(terminal_nodes_with_reward_1, key=lambda node: node.value)
        all_nodes_list = collect_all_nodes(root)
        all_nodes_list.extend(terminals)
        best_child = max(all_nodes_list, key=lambda x: x.reward)
        failed_trajectories = []
        if best_child.reward == 1:
            logging.info("Successful trajectory found")
        else:
            logging.info("No successful trajectory found")
        if best_child is None:
            best_child = root
        best_child.set_state(CtxState.Success)
        return best_child

    def run(self, image_loc: str, additional: str = ""):
        """
        Run the agent
        :param image_loc: path to the image
        :param additional: additional context to the agent
        :return:
        """
        utils.flush_run_dir()
        ctx = Context(tools=TOOLS)
        ctx.add_message(
            Message(
                INITIAL_REACT_PROMPT.format(
                    tool_names=", ".join([t.name for t in TOOLS]),
                    tools=render_text_description(TOOLS),
                    input=f"{utils.image_to_prompt(image_loc)} Where is this image located? {additional}",
                )
            )
        )
        for i in range(1, self.DEPTH_THRESHOLD + 1):
            print("last message", ctx.messages[-1].message)
            choices = self.vllm.prompt(ctx, stop=["Observation"], n=self.BRANCH_CNT, temperature=1)
            for (i, r) in enumerate(choices):
                print(f"Branch {i}: {r}")
            chosen = int(input("Choose a branch: "))
            res = choices[chosen].message
            parsed: AgentAction | AgentFinish = self.output_parser.parse(res)
            if isinstance(parsed, AgentFinish):
                isok = input("Is this ok? (y/n)")
                if isok == "y":
                    print("Finished !")
                    break
                feedback = input("Enter feedback:")
                res += "\nFeedback: " + feedback
                ctx.add_message(Message(f"{res}\Analyze{i}: "))
            elif isinstance(parsed, AgentAction):
                print("[blue]Action[/blue]: ", parsed.tool)
                print("[blue]Action Input[/blue]: ", parsed.tool_input)
                tool: BaseTool | None = find_tool(parsed.tool)
                if tool is None:
                    ctx.add_message(
                        Message(
                            f"{res}\n Could not find tool {parsed.tool}, please adjust your input. \nAnalyze{i}: "
                        )
                    )
                    continue
                try:
                    tool_res = str(
                        tool._run(*utils.get_args(tool, utils.sanitize(parsed.tool_input)))
                    )  # TODO: Make multi-argument parsing more robust
                except Exception as e:
                    print(f"Exception encountered when running tool {tool}", e)
                    # ask if user would like to continue, if so, ask for potential feedback
                    docontinue = input("Continue? (y/n)")
                    if docontinue == "n":
                        break
                    feedback = input("Enter feedback if any:")
                    ctx.add_message(
                        Message(
                            f"{res}\n Could not run tool {parsed.tool}: {e}, {feedback}\n please adjust. \nAnalyze{i}: "
                        )
                    )
                    continue
                if tool.return_direct:
                    isok = input("Is this ok? (y/n)")
                    if isok == "y":
                        print("Finished !")
                        break
                    feedback = input("Enter feedback:")
                    tool_res += "\nFeedback: " + feedback
                ctx.add_message(
                    Message(f"{res}\nObservation{i}: {tool_res}\nAnalyze{i}: ")
                )
                ctx.commit(transition=parsed)


if __name__ == "__main__":
    srv, sub_thread = start_srv()
    sio_sub = SIOSubscriber(srv)
    agent = Agent(Gpt4Vision(debug=True), subscriber=sio_sub)
    additional_info = input(
        "Enter any additional information regarding this image or guidance on the geolocation process. \nPress enter to begin.\n"
    )
    logging.basicConfig(level=logging.INFO)
    img_loc = sys.argv[1] if len(sys.argv) else "./images/anon/12.png"
    res = agent.lats(img_loc, additional_info)
    print(res)
    input("success! Press enter to exit.")
