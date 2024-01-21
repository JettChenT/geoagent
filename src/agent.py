from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.tools.render import render_text_description
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
from rich import print

from . import config, utils
from .prompting import *
from .connector.gptv import Gpt4Vision
from .connector import LMM, Message
from .tools import TOOLS, find_tool
from .context import Context


class Agent:
    DEPTH_THRESHOLD = 10
    BRANCH_CNT = 3

    def __init__(self, vllm: LMM):
        self.vllm = vllm
        self.depth = 0
        self.output_parser = ReActSingleInputOutputParser()

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
            choices = self.vllm.prompt(ctx, stop=["Observation"], n=self.BRANCH_CNT)
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
                tool_res = str(
                    tool._run(*utils.get_args(tool, utils.sanitize(parsed.tool_input)))
                )  # TODO: Make multi-argument parsing more robust
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
    agent = Agent(Gpt4Vision())
    additional_info = input(
        "Enter any additional information regarding this image or guidance on the geolocation process. \nPress enter to begin.\n"
    )
    print(agent.run("./images/anon/2.png", additional_info))
