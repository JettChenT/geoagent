from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import re
from .. import utils
from pathlib import Path
from ..tools import TOOLS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools.render import render_text_description
from langchain.tools import BaseTool
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from rich import print
import dotenv

dotenv.load_dotenv()


def proc_messages(messages: list[Message]) -> HumanMessage:
    """
    Process messages from the chat history to a HumanMessage object. Cuz Gemini does not support chat mode yet.
    :param messages:
    :return:
    """
    comb = "".join([m.message for m in messages])
    img_tag_pattern = re.compile(r"<img (.*?)>")
    img_tags = img_tag_pattern.findall(comb)
    blocks = img_tag_pattern.split(comb)
    output = []
    for block in blocks:
        if block == "":
            continue
        if block in img_tags:
            image_object = {
                "type": "image_url",
                "image_url": {
                    "url": utils.proc_image_url(block),
                },
            }
            output.append(image_object)
        else:
            output.append({"type": "text", "text": block})
    return HumanMessage(content=output)


chat = ChatGoogleGenerativeAI(model="gemini-pro-vision")
output_parser = ReActSingleInputOutputParser()
MAX_ITER = 10
tools_map = {tool.name: tool for tool in TOOLS}


def find_tool(name: str) -> BaseTool:
    for tool in TOOLS:
        if tool.name in name:
            return tool


def main(image_loc):
    utils.flush_run_dir()
    messages = [
        Message(
            INITIAL_REACT_PROMPT.format(
                tool_names=", ".join([t.name for t in TOOLS]),
                tools=render_text_description(TOOLS),
                input=f"{utils.image_to_prompt(image_loc)} Where is this image located?",
            )
        )
    ]
    for i in range(1, MAX_ITER + 1):
        print("current messages", messages[1:])
        cur_m = [proc_messages(messages)]
        res = chat.invoke(cur_m, stop=["Observation"]).content
        parsed: AgentAction | AgentFinish = output_parser.parse(res)
        if isinstance(parsed, AgentFinish):
            print(res)
            isok = input("Is this ok? (y/n)")
            if isok == "y":
                print("Finished !")
                break
            feedback = input("Enter feedback:")
            res += "\nFeedback: " + feedback
            messages.append(Message(f"{res}\Analyze{i}: "))
        elif isinstance(parsed, AgentAction):
            print("[blue]Action[/blue]: ", parsed.tool)
            print("[blue]Action Input[/blue]: ", parsed.tool_input)
            tool: BaseTool | None = find_tool(parsed.tool)
            if tool is None:
                messages.append(
                    Message(
                        f"{res}\n Could not find tool {parsed.tool}, please adjust your input. \nAnalyze{i}: "
                    )
                )
            tool_res = str(tool._run(utils.sanitize(parsed.tool_input)))
            if tool.return_direct:
                isok = input("Is this ok? (y/n)")
                if isok == "y":
                    print("Finished !")
                    break
                feedback = input("Enter feedback:")
                tool_res += "\nFeedback: " + feedback
            messages.append(Message(f"{res}\nObservation{i}: {tool_res}\nAnalyze{i}: "))


if __name__ == "__main__":
    main("./images/kns.png")
