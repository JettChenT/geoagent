from typing import Optional, List, Dict

from attrs import define, field, Factory
from langchain_core.tools import BaseTool

from .context import Context
from .subscriber import Subscriber


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
            if tool.name in name:
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
            # self._push("set_session_info", (
            #     self.id,
            #     self.to_json()
            # ))
            return res

        return wrapper

    def get_loc(self, identifier: str):
        try:
            return self.namespace[identifier]
        except KeyError:
            raise Exception(f"Could not find {identifier} in namespace.")

    @notify_update
    def add_reflection(self, reflection: str):
        self.reflections.append(reflection)

    @notify_update
    def add_conclusion(self, conclusion: str):
        self.conclusions.append(conclusion)

    @notify_update
    def update(self):
        return
