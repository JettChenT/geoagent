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

dotenv.load_dotenv()
chat = ChatOpenAI(model="gpt-4-vision-preview", max_tokens=3000)
tools = load_tools(["llm-math"], llm=chat)

REACT_PROMPT = """Answer the following questions as best you can. You have access to the following tools:\n\n{tools}\n\nUse the following format:\n\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction: the action to take, should be one of [{tool_names}]\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question\n\nBegin!\n\nQuestion: {input}\nThought:{agent_scratchpad}'"""

template = ChatPromptTemplate.from_messages(
    [
        ("human",
        [
            {"type":"text", "text": REACT_PROMPT},
            {"type": "image_url", "image_url": "{image_url}"}
        ])
    ]
)

prompt = template.partial(
            tools=render_text_description(tools),
            tool_names=", ".join([t.name for t in tools]),
        )

llm_with_stop = chat.bind(stop=["\nObservation"])

print(llm_with_stop)
agent = (
    {
        "input": lambda x: x["input"],
        "image_url": lambda x: x["image_url"],
        "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
    }
    | prompt
    | llm_with_stop
    | ReActSingleInputOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def tst_agent():
    res = agent_executor.invoke(
        {
            "input": "The image shows a physics problem. Read it and solve it.",
            "image_url": encode_image(Path('./images/hw_prob.png')),
        }
    )

    print(res)

tst_agent()