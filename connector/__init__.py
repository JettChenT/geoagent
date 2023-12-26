from typing import List, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel


class Message(BaseModel):
    message: str
    role: str | None

    def __init__(self, msg, role: str | None = None):
        super().__init__(message=msg, role=role)

class Context(BaseModel):
    messages: List[Message]
    tools: List[BaseTool]

    def __init__(self, tools: List[BaseTool] | None = None):
        super().__init__(messages=[], tools=tools or [])

    def add_message(self, msg: Message):
        self.messages.append(msg)

class LMM:
    def prompt(self, context: Context, stop: Optional[List[str]]) -> Message:
        pass

    def heartbeat(self) -> bool:
        pass