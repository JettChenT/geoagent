from pathlib import Path
from typing import List, Tuple

from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.tools.render import render_text_description
from langchain.agents import AgentExecutor
import dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_core.agents import AgentAction
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from ..utils import encode_image
from ..tools import TOOLS
from langchain.globals import set_debug

# set_debug(True)
dotenv.load_dotenv()
chat = ChatGoogleGenerativeAI(model="gemini-pro-vision")
tools = TOOLS


def fmt_log(
    intermediate_steps: List[Tuple[AgentAction, str]],
) -> str:
    """Construct the scratchpad that lets the agent continue its thought process."""
    thoughts = ""
    for i, obj in enumerate(intermediate_steps):
        action, observation = obj
        t = i + 1
        thoughts += action.log
        thoughts += f"\nObservation{t}: {observation}\nAnalyze{t}: "
    return thoughts


REACT_PROMPT = """Answer the following questions as best you can. You have access to the following tools:

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

Question1: {input}
Thought1: {agent_scratchpad}"""

cnt = 0


def get_cnt():
    global cnt
    cnt += 1
    return cnt


template = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            [
                {"type": "image_url", "image_url": "{image_url}"},
                {"type": "text", "text": REACT_PROMPT},
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
agent = (
    {
        "input": lambda x: x["input"],
        "image_url": lambda x: x.get("image_url"),
        "agent_scratchpad": lambda x: fmt_log(x["intermediate_steps"]),
    }
    | prompt
    | llm_with_stop
    | ReActSingleInputOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def tst_agent():
    res = agent_executor.invoke(
        {
            "input": "Where is this image located?",
            "image_url": "https://ik.imagekit.io/sfwall/NY5_J2A4Si6Z6.png?updatedAt=1702987667392",
        }
    )

    print(res)


def tst_chat():
    imurl = "https://ik.imagekit.io/sfwall/NY5_J2A4Si6Z6.png?updatedAt=1702987667392"
    inp = [
        HumanMessage(
            content=[
                {"type": "image_url", "image_url": imurl},
                {
                    "type": "text",
                    "text": '\nAnswer the following questions as best you can. You have access to the following tools:\n\nOverpass Turbo: Overpass Turbo(q: str) -> Any - Skims through the query string for a chunk of OSM Query, executes the query, and returns the resulting\n  lat long pairs. For example, a valid input would be:\n  \'\'\'\n  area["name"~".*Washington.*"];\nway["name"~"Monroe.*St.*NW"](area) -> .mainway;\n\n(\n nwr(around.mainway:500)["name"~"Korean.*Steak.*House"];\n\n // Find nearby businesses with CA branding\n nwr(around.mainway:500)["name"~"^CA.*"];\n\n // Look for a sign with the words "Do not block"\n node(around.mainway:500)["traffic_sign"~"Do not block"];\n);\n\nout center;\n  \'\'\'\n  Do not include a codeblock in function call. Jus the raw query.\n  :param q: The overpass turbo query you are running. ALWAYS pass in a full overpass turbo query.\n  :return: list of tuples if valid, otherwise returns a string representing the next prompt\nOSM Wiki Search: OSM Wiki Search(query: str) -> str - Searches the OSM Wiki for a query. Use this if you are not sure about\n  specific features or tags that you would use for your later Overpass Turbo Query.\n  :param query:\n  :return:\nNomantim Geocoder: Nomantim Geocoder(query: str) -> str - Searches the OSM Wiki for a query. Use this if you are not sure about\n  what are the Open Streetmap names for a general location.\n  Priorize using this if you need an area name such as `United States` or `Washington`.\n  Prefer not to use this if you are looking up a specific string or name, for that use Overpass Turbo.\n  :param query: A single area or location you want to geocode for.\n  :return:\n\nUse the following format:\n\nQuestion1: The overall guideline to what you are going to do\nThought1: Think about what you should do\nAction1: the action to take, should be one of [Overpass Turbo, OSM Wiki Search, Nomantim Geocoder]\nAction Input1: the input to the action1\nObservation1 : the result of the action1\nAnalyze1: Analyze the results of action1\nThought2: Think about what you should do based on analyze1\nAction2: the action to take, should be one of [Overpass Turbo, OSM Wiki Search, Nomantim Geocoder]\nAction Input2: the input to the action2\nObservation2: the result of the action2\nAnalyze2: Analyze the results of action2\nThought3: So on...\n\nBegin!\n\nQuestion1: Where is this image located?\nThought1: ',
                },
            ]
        )
    ]
    res = chat.invoke(inp, stop=["Observation"])
    print(res)


tst_agent()
