import functools
from typing import List, Optional
from pathlib import Path
import json
import hashlib
from enum import Enum
from contextlib import contextmanager

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
from typing_extensions import Self
from .subscriber import Subscriber, SubscriberMessageType
import numpy as np

class Message:
    def __init__(self, msg: str, role: str | None = None):
        self.message = msg
        self.role = role

    def __repr__(self):
        return f"Message({self.message}, {self.role})"

    def to_json(self):
        return {
            "message": self.message,
            "role": self.role
        }

class CtxState(Enum):
    Normal = 'normal'
    Running = 'running'
    Expanding = 'expanding'
    Evaluating = 'evaluating'
    Rollout = 'rollout'
    Success = 'success'
    Reflecting = 'reflecting'

class Context:
    """
    Context represents the state of an agent.
    In the frame of a LATS search, this can also be seen as a node of the search tree.
    """

    def __init__(self,
                 parent: Self | None = None,
                 cur_messages: List[Message] | None = None,
                 transition: Optional[AgentAction] = None,
                 observation=None,
                 subscriber: Optional[Subscriber] = None,
                 state: CtxState = CtxState.Normal
                 ):
        self.cur_messages = cur_messages or []
        self.transition = transition  # The last action or action-equivalent taken by the agent
        self.observation = observation  # The last observation made by the agent
        self.subscriber = subscriber
        self.run_state = state
        self.auxiliary = {}

        # LATS stuff
        self.parent = parent
        self.visits = 0
        self.value = 0
        self.children: List[Self] = []
        self.depth = 0 if parent is None else parent.depth + 1
        self.is_terminal = False
        self.reward = 0.0
        self.exhausted = False  # If all children are terminal
        self.em = 0  # Exact match, evaluation metric

        if self.parent:
            self._push(SubscriberMessageType.AddNode, (
                hex(id(self.parent)),
                hex(id(self)),
                self.to_json()
            ))
        else:
            self._push(SubscriberMessageType.RootNode, (
                    hex(id(self)),
                    self.to_json()
                ))

    def uct(self):
        if self.visits == 0:
            return self.value
        return self.value / self.visits + np.sqrt(2 * np.log(self.parent.visits) / self.visits)

    @staticmethod
    def notify_update(func):
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self._push(SubscriberMessageType.UpdateNode, (
                hex(id(self)),
                self.to_json()
            ))
            return res

        return wrapper

    @notify_update
    def add_message(self, msg: Message):
        self.cur_messages.append(msg)

    @notify_update
    def add_messages(self, messages: List[Message]):
        self.cur_messages.extend(messages)

    def commit(self, message: List[Message] | Message | None = None, transition=None) -> Self:
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
            parent=self,
            cur_messages=message,
            transition=transition,
            subscriber=self.subscriber
        )
        self.children.append(res)
        return res

    def digest(self):
        return hashlib.md5(str(self.messages).encode()).hexdigest()

    def to_json(self):
        transition = {
            "type": "NO_ACTION"
        }
        match self.transition:
            case AgentAction():
                transition = {
                    "type": "AgentAction",
                    "tool": self.transition.tool,
                    "tool_input": self.transition.tool_input
                }
            case AgentFinish():
                transition = {
                    "type": "AgentFinish",
                    "return_values": self.transition.return_values,
                }
        return {
            "cur_messages": [m.to_json() for m in self.messages],
            "transition": transition,
            "observation": self.observation,
            "state": self.run_state.value,
            "lats_data": {
                "visits": self.visits,
                "value": self.value,
                "depth": self.depth,
            },
            "auxiliary": self.auxiliary
        }

    def serialize_recursive(self):
        res = {
            "context": self.to_json(),
        }
        if self.children:
            res["children"] = [c.serialize_recursive() for c in self.children]
        return res

    def _push(self, msg_type: SubscriberMessageType, msg):
        if self.subscriber:
            self.subscriber.push(msg_type, msg)

    def dump(self, dst: Path | None = None):
        """
        Dump the context to a json file
        :param dst:
        :return:
        """
        dat = {
            "messages": [m.to_json() for m in self.messages],
            "transition": str(self.transition),
            "value": self.value,
            "visits": self.visits,
        }
        with open(dst, 'w') as f:
            json.dump(dat, f)

    @staticmethod
    def load(src: Path) -> Self:
        with open(src, 'r') as f:
            dat = json.load(f)
            messages = [Message(m['message'], m['role']) for m in dat['messages']]
            ctx = Context(
                cur_messages=messages,
                transition=dat['transition'],
            )
            ctx.value = dat['value']
            ctx.visits = dat['visits']
            return ctx

    @property
    def messages(self) -> List[Message]:
        return (self.parent.messages if self.parent else []) + self.cur_messages

    @notify_update
    def set_observation(self, obs):
        self.observation = obs

    @notify_update
    def set_auxiliary(self, key, value):
        self.auxiliary[key] = value

    @notify_update
    def update_auxiliary(self, data):
        self.auxiliary.update(data)

    @notify_update
    def set_state(self, state: CtxState):
        self.run_state = state

    @notify_update
    def notify(self):
        return

    @staticmethod
    def wrap_state(state: CtxState):
        def wrapper(func):
            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                possible_nodes = ([arg for arg in args if isinstance(arg, Context)]
                                  + [v for v in kwargs.values() if isinstance(v, Context)])
                if not possible_nodes:
                    return func(*args, **kwargs)
                node = possible_nodes[0]
                prev_state = node.run_state
                node.set_state(state)
                res = func(*args, **kwargs)
                node.set_state(prev_state)
                return res

            return wrapped

        return wrapper

    def id(self):
        return hex(id(self))

    def __str__(self):
        transition_render = 'NO_ACTION'
        if isinstance(self.transition, AgentAction):
            transition_render = f"{self.transition.tool} ({repr(self.transition.tool_input)})"
        if isinstance(self.transition, AgentFinish):
            transition_render = f"FINISH"
        return (f"Context([yellow]{hex(id(self))}[/yellow] ;"
                f"[blue]{self.run_state.value}[/blue],"
                f"[green]{transition_render}[/green], "
                f"value: [red]{self.value}[/red], visits: [red]{self.visits}[/red], "
                f"depth: [blue]{self.depth}[/blue], reward: [blue]{self.reward}[/blue]) :: "
                f"[blue] {repr(self.cur_messages[-1].message[-30:])} [/blue]")
