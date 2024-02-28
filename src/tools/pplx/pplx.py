from openai import OpenAI
from ... import config
from langchain.tools import tool
from functools import cache
import os

PPLX_KEY = os.getenv("PPLX_KEY")
client = OpenAI(api_key=PPLX_KEY, base_url="https://api.perplexity.ai")

@tool("perplexity ask")
@cache
def ask(question: str) -> str:
    """
    Ask a question to the perplexity online model. Use this as a search engine.
    Note that it does not have access to image. Only send text queries that do not require visual information.
    :param question: the question to ask
    :return:
    """
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": question
        }
    ]
    response = client.chat.completions.create(
        model="pplx-7b-online",
        messages=messages
    )
    return response.choices[0].message.content

if __name__ == '__main__':
    print(ask("What is the coordinates for Apple HQ?"))
