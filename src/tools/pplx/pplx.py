from openai import OpenAI
from ... import config
from ..wrapper import gtool, ToolResponse
from langchain.tools import tool
from functools import cache
import os

PPLX_KEY = os.getenv("PPLX_KEY")
client = OpenAI(api_key=PPLX_KEY, base_url="https://api.perplexity.ai")

@gtool("perplexity ask", cached=True)
def ask(question: str) -> ToolResponse:
    """
    Ask a question to the perplexity online model. Use this as a search engine.
    Note that it does not have access to image. Only send text queries that do not require visual information.
    :param question: the question to ask
    :return:
    """
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant helping with a geolocation investigation. "
            "If a precise location relating to the query can be found, please output the exact address or coordinates. "
        },
        {
            "role": "user",
            "content": question
        }
    ]
    response = client.chat.completions.create(
        model="sonar-medium-online",
        messages=messages
    )
    res = response.choices[0].message.content
    return ToolResponse(res, {"text": res})

if __name__ == '__main__':
    print(ask("What is the location of the building fire in Shebekino, Belgorod region, Russia? Give me the address."))
