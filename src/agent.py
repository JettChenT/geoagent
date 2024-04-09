import os
import sys
from pathlib import Path
from typing import Tuple, Optional, List
from enum import Enum
import re
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, wait

from langchain.tools.render import render_text_description
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
import traceback
from rich import print

from . import config, utils
from .prompting import *
from .connector.gptv import Gpt4Vision
from .connector.fast_lm import Gpt35
from .connector import LMM, Message
from .messages import ProxiedMessage
from .tools import TOOLS, proc_tools, ToolResponse
from .context import Context, CtxState
from .session import Session
from .react_parser import ReActSingleInputOutputParser
from .subscriber import Subscriber, SIOSubscriber, default_subscriber

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
    ROLLOUT_THRESHOLD = 8
    BRANCH_CNT = 5
    RESCUE_THRESHOLD = 3

    def __init__(self, vllm: LMM, run_type: RunType = RunType.PARALLEL, subscriber: Optional[Subscriber] = None, fast_lm : Optional[LMM]=None):
        self.vllm = vllm
        self.fast_lm = fast_lm or vllm
        self.output_parser = ReActSingleInputOutputParser()
        self.run_type = run_type
        subscriber = subscriber or default_subscriber()
        self.subscriber = subscriber
        self.session = Session(subscriber=subscriber)

    def _push(self, *args, **kwargs):
        if self.subscriber:
            self.subscriber.push(*args, **kwargs)

    def backup(self):
        os.mkdir(f'bak/{self.session.id}')
        with open(f'bak/{self.session.id}/root.json', 'w') as f:
            f.write(str(self.session.root.serialize_recursive()))
        os.system(f'cp -r run/{self.session.id} bak/{self.session.id}')

    @Context.wrap_state(CtxState.Expanding)
    def expand_node(self, node: Context):
        logging.info(f"expanding node {hex(id(node))}.....")
        if node.depth >= self.DEPTH_THRESHOLD:
            node.is_terminal = True
            return
        sampled = self.vllm.prompt(node, self.session, stop=["Observation"], n=self.BRANCH_CNT)
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
        tool: BaseTool | None = self.session.find_tool(state.transition.tool)
        if tool is None:
            fail_cnt = 0
            while fail_cnt <= self.RESCUE_THRESHOLD:
                try:
                    tool = self.session.find_tool(
                        self.fast_lm.prompt(
                            [Message(FUNCTION_NOT_FOUND_PROMPT.format(functions=", ".join([t.name for t in self.session.tools]), used_function=state.transition.tool))],
                            self.session
                        )[0].message.splitlines()[-1]
                    )
                    break
                except Exception as e:
                    fail_cnt += 1
            if tool is None:
                state.add_message(
                    Message(
                        f"Could not find tool {state.transition.tool}, please adjust your input. \nAnalyze{state.depth}: "
                ))
                return
        try:
            tool_inp = state.transition.tool_input
            orig_inp = tool_inp
            orig_e = None
            fail_cnt = 0
            tool_res = None
            attempts = []
            while fail_cnt <= self.RESCUE_THRESHOLD:
                try:
                    tool_res: ToolResponse = tool._run(*utils.get_args(tool, utils.sanitize(tool_inp)))
                    break
                except Exception as e:
                    if orig_e is None:
                        orig_e = e
                    if fail_cnt == self.RESCUE_THRESHOLD:
                        raise e
                    fail_cnt += 1
                    rescut_pmpt = [Message(RESCUE_PROMPT.format(function_description=tool.description, inputs=tool_inp, error_message=str(e), attempts=attempts))]
                    tool_inp = self.fast_lm.prompt(
                        rescut_pmpt,
                        self.session
                    )[0].message.splitlines()[-1]
                    if "give_up" in tool_inp.lower():
                        tool_inp = orig_inp
                        raise orig_e
                    attempts.append(f"Attempt {fail_cnt}: tool input = {tool_inp}, error = {str(e)} \n")
        except Exception as e:
            print('[red]Error[/red]: ', e, traceback.format_exc())
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

        if tool_res.auxiliary:
            state.update_auxiliary(tool_res.auxiliary)

        if tool.return_direct:
            state.is_terminal = True
            if self.run_type == RunType.INTERACTIVE:
                isok = input("Is this ok? (y/n)")
                if isok == "y":
                    state.reward = 1
                else:
                    feedback = input("Enter feedback:")
                    tool_res.raw += "\nFeedback: " + feedback
            else:
                state.reward = self.get_reward(state)
        state.add_message(
            Message(f"Observation{state.depth}: {tool_res.raw}\nAnalyze{state.depth}: ")
        )
        state.set_observation(tool_res.raw)

    @Context.wrap_state(CtxState.Evaluating)
    def get_value(self, node: Context):
        messages = node.messages
        messages.append(Message(VALUE_PROMPT))
        res = self.vllm.prompt(messages, self.session, temperature=0.1)[0]
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
        res = self.vllm.prompt(messages, self.session, temperature=0.1)[0]
        lines = res.message.splitlines()
        targ_lines = [line for line in lines if re.match(r"branch\s+(\d+):\s+(\d+)", line)]
        print('targ lines: ', targ_lines)
        if len(targ_lines) < len(nodes):
            logging.warning("Could not find all values in prompt")
            targ_lines += ['0'] * (len(nodes) - len(targ_lines))
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
        res = self.vllm.prompt(messages, self.session, temperature=0.1)[0]
        targ_line = res.message.splitlines()[-1]
        for i in range(10, 0, -1):
            if str(i) in targ_line:
                logging.info(f"Found value {i} in {targ_line}")
                node.set_auxiliary("reward", i / 10)
                return i / 10
        return 0

    @Context.wrap_state(CtxState.Reflecting)
    def get_reflection(self, node: Context):
        messages = node.messages
        messages.append(Message(REFLECTION_PROMPT))
        res = self.vllm.prompt(messages, self.session)[0]
        node.set_auxiliary("reflection", res.message)
        self.session.add_reflection(res.message)

    def image_pmpt(self, loc: str | Path , additional: str = "") -> str:
        image_loc = utils.enforce_image(loc, self.session)
        self._push("set_session_info_key", (self.session.id, "image_loc", image_loc))
        return f"{utils.image_to_prompt(image_loc, self.session)} Where is this image located? {additional}"

    def lats(self, goal: str, set_cur=False) -> Context:
        self._push("global_info_set", ("latest_session", self.session.id))
        if set_cur:
            self._push("set_current_session", self.session.id)
        self.session.tools = proc_tools(TOOLS, self.session)
        root = Context(subscriber=self.subscriber)
        initial_msg = [
            Message(
                INITIAL_REACT_PROMPT.format(
                    tool_names=", ".join([t.name for t in self.session.tools]),
                    tools=render_text_description(self.session.tools),
                    input=goal,
                )
            ),
            ProxiedMessage(
                lambda ses: f"Conclusions Reached: {';'.join(ses.conclusions)}\n"
                            f"Reflections: {';'.join(ses.reflections)}\n"
                            f"Available directory of access: run/{ses.id}\n"
                            f"Available ids in namespace: {list(ses.namespace.keys())}\n",
                self.session
            )
        ]
        root.add_messages(initial_msg)
        self.session.root = root
        self._push("set_session_id", (root.id(), self.session.id))
        terminals = []

        for i in range(1, self.DEPTH_THRESHOLD + 1):
            node = select_node(root)
            logging.info(f"Selected node at depth {node.depth}: {node.messages[-1]}")
            print("-----Before expansion-----")
            print_tree(root, highlight=node)
            self.expand_node(node)
            print("-----After expansion-----")
            print_tree(root)
            if len(node.children) == 0:
                logging.info(f"No children found for node {node}")
                continue
            values = self.get_values(node.children)
            if len(values) == 0:
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
            self.get_reflection(terminal)
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


def default_agent(sio):
    sub = default_subscriber(sio)
    agent = Agent(Gpt4Vision(debug=True), subscriber=sub, fast_lm=Gpt35(debug=True))
    return agent

def main():
    sub = default_subscriber()
    agent = Agent(Gpt4Vision(debug=True), subscriber=sub)
    additional_info = input(
        "Enter any additional information regarding this image or guidance on the geolocation process. \nPress enter to begin.\n"
    )
    sub.push("global_info_set", ("task", "Geolocating Image"))
    logging.basicConfig(level=logging.INFO)
    img_loc = sys.argv[1] if len(sys.argv) else "./images/anon/12.png"
    res = agent.lats(agent.image_pmpt(img_loc, additional_info))
    print(res)
    input("success! Press enter to exit.")


if __name__ == '__main__':
    main()
