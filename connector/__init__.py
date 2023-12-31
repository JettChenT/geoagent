from typing import List, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel
from attrs import define


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

class LMM:
    def prompt(self, context: Context, stop: Optional[List[str]]) -> Message:
        pass

    def heartbeat(self) -> bool:
        pass