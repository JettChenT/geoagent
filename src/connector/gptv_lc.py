from pathlib import Path
from typing import Any, Dict, Optional, List

from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.tools.render import render_text_description
from langchain.agents import AgentExecutor
import dotenv
from langchain.prompts import PromptTemplate, ChatPromptTemplate

from utils import encode_image
from tools import TOOLS
import prompting

dotenv.load_dotenv()
chat = ChatOpenAI(model="gpt-4-vision-preview", max_tokens=3000)
tools = TOOLS

REACT_PROMPT = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question1: The overall guideline to what you are going to do
Thought1: Think about what you should do
Action1: the action to take, should be one of [{tool_names}]
Action Input1: the input to the action1
Observation1 : the result of the action1
Analyze1: Analyze the results of action1
Thought2: Think about what you should do based on analyze1
Action2: the action to take, should be one of [{tool_names}]
Action Input2: the input to the action2
Observation2: the result of the action2
Analyze2: Analyze the results of action2
Thought3: So on...

Begin!

Question{n}: {input}
Thought{n}: {agent_scratchpad}
"""

template = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            [
                {"type": "text", "text": REACT_PROMPT},
                {"type": "image_url", "image_url": "{image_url}"},
            ],
        )
    ]
)

prompt = template.partial(
    tools=render_text_description(tools),
    tool_names=", ".join([t.name for t in tools]),
)

llm_with_stop = chat.bind(stop=["\nObservation"])

print(llm_with_stop)

cnt = 0


def get_cnt():
    global cnt
    cnt += 1
    return cnt


agent = (
    {
        "input": lambda x: x["input"],
        "image_url": lambda x: x["image_url"],
        "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        "n": lambda _: str(get_cnt()),
    }
    | prompt
    | llm_with_stop
    | ReActSingleInputOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def test_agent_iterative():
    initial = {
        "input": prompting.TOOL_PROMPT,
        "image_url": encode_image(Path("./images/phoenix_taylor.png")),
    }
    intermediate_steps = []
    n = 1
    while True:
        output = agent.invoke()
    return


def test_agent():
    res = agent_executor.invoke(
        {
            "input": prompting.TOOL_PROMPT,
            "image_url": encode_image(Path("./images/phoenix_taylor.png")),
        }
    )

    print(res)


test_agent()
