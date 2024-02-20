from openai import OpenAI
from ... import config
from langchain.tools import tool
import os

PPLX_KEY = os.getenv("PPLX_KEY")
client = OpenAI(api_key=PPLX_KEY, base_url="https://api.perplexity.ai")

@tool("perplexity ask")
def ask(question: str):
    """
    Ask a question to the perplexity online model
    :param question:
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
    print(ask("What is the capital of France?"))
