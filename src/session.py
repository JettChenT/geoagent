from typing import Optional, List, Dict

from attrs import define, field, Factory
from pathlib import Path
from langchain_core.tools import BaseTool
from typing import Self

from .config import RUN_DIR
from .context import Context
from .subscriber import Subscriber, SubscriberMessageType


@define
class Session:
    conclusions: List[str] = Factory(list)
    failed_trajectories: List[Context] = Factory(list)
    reflections: List[str] = Factory(list)
    root: Optional[Context] = None
    tools: List[BaseTool] = Factory(list)
    subscriber: Subscriber = Factory(Subscriber)
    namespace: Dict = Factory(dict)

    @property
    def id(self):
        return str(hex(id(self)))

    def find_tool(self, name: str) -> BaseTool | None:
        for tool in self.tools:
            if tool.name in name or tool._run.__name__ in name:
                return tool

    def to_json(self):
        return {
            "conclusions": self.conclusions,
            "failed_trajectories": [t.to_json() for t in self.failed_trajectories],
            "reflections": self.reflections,
            "root": self.root.id(),
        }

    @staticmethod
    def notify_update(func):
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self.subscriber.push(SubscriberMessageType.SetSessionInfo, (
                self.id,
                self.to_json()
            ))
            return res

        return wrapper

    def update_info(self, delta: Dict):
        self.subscriber.push(SubscriberMessageType.SetSessionInfo, (
            self.id,
            delta
        ))

    def get_loc(self, identifier: str):
        try:
            return self.namespace[identifier]
        except KeyError:
            raise Exception(f"Could not find {identifier} in namespace.")
    
    def setup(self) -> Self:
        p = Path(RUN_DIR) / self.id
        p.mkdir(parents=True, exist_ok=True)
        return self

    @notify_update
    def add_reflection(self, reflection: str):
        self.reflections.append(reflection)

    @notify_update
    def add_conclusion(self, conclusion: str):
        self.conclusions.append(conclusion)

    @notify_update
    def update(self):
        return
