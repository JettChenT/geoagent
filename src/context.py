from typing import List

from langchain_core.tools import BaseTool


class Message:
    message: str
    role: str | None

    def __init__(self, msg, role: str | None = None):
        self.message = msg
        self.role = role


class Context:
    messages: List[Message]
    tools: List[BaseTool]

    def __init__(self, tools: List[BaseTool] | None = None):
        self.tools = tools
        self.messages = []

    def add_message(self, msg: Message):
        self.messages.append(msg)
