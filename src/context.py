from typing import List

from langchain_core.tools import BaseTool
from typing_extensions import Self


class Message:
    message: str
    role: str | None

    def __init__(self, msg, role: str | None = None):
        self.message = msg
        self.role = role

    def __repr__(self):
        return f"Message({self.message}, {self.role})"


class Context:
    """
    Context represents the state of an agent.
    """
    def __init__(self,
                 tools: List[BaseTool] | None = None,
                 parent: Self|None = None,
                 cur_messages: List[Message] | None = None,
                 transition = None
                 ):
        self.tools = tools
        self.parent = parent
        self.cur_messages = cur_messages or []
        self.transition = transition # The last action or action-equivalent taken by the agent

    def add_message(self, msg: Message):
        self.cur_messages.append(msg)

    def commit(self, message: List[Message] | Message | None = None, transition = None) -> Self:
        """
        Commit the context to a new one. Used for state transitions
        :param message:
        :param transition:
        :return:
        """
        if message is None:
            message = []
        elif isinstance(message, Message):
            message = [message]
        return Context(
            tools=self.tools,
            parent=self,
            cur_messages=message,
            transition=transition
        )

    @property
    def messages(self):
        return (self.parent.messages if self.parent else []) + self.cur_messages
