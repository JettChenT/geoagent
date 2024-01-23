from typing import List, Optional

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
from typing_extensions import Self
import numpy as np


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
    In the frame of a LATS search, this can also be seen as a node of the search tree.
    """
    def __init__(self,
                 tools: List[BaseTool] | None = None,
                 parent: Self|None = None,
                 cur_messages: List[Message] | None = None,
                 transition: Optional[AgentAction]=None,
                 observation=None
                 ):
        self.tools = tools
        self.cur_messages = cur_messages or []
        self.transition = transition # The last action or action-equivalent taken by the agent
        self.observation = observation # The last observation made by the agent

        # LATS stuff
        self.parent = parent
        self.visits = 0
        self.value = 0
        self.children: List[Self] = []
        self.depth = 0 if parent is None else parent.depth + 1
        self.is_terminal = False
        self.reward = 0
        self.exhausted = False  # If all children are terminal
        self.em = 0  # Exact match, evaluation metric

    def uct(self):
        if self.visits == 0:
            return self.value
        return self.value / self.visits + np.sqrt(2 * np.log(self.parent.visits) / self.visits)

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
        res = Context(
            tools=self.tools,
            parent=self,
            cur_messages=message,
            transition=transition
        )
        self.children.append(res)
        return res

    @property
    def messages(self):
        return (self.parent.messages if self.parent else []) + self.cur_messages

    def __str__(self):
        transition_render = 'NO_ACTION'
        if isinstance(self.transition, AgentAction):
            transition_render = f"{self.transition.tool} ({repr(self.transition.tool_input)})"
        if isinstance(self.transition, AgentFinish):
            transition_render = f"FINISH"
        return (f"Context([yellow]{hex(id(self))}[/yellow] ;"
                f"[green]{transition_render}[/green], "
                f"value: [red]{self.value}[/red], visits: [red]{self.visits}[/red], "
                f"depth: [blue]{self.depth}[/blue], reward: [blue]{self.reward}[/blue]) :: "
                f"[blue] {repr(self.cur_messages[-1].message[-30:])} [/blue]")