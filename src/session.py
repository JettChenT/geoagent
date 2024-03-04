from typing import Optional, List

from attrs import define, field, Factory
from langchain_core.tools import BaseTool

from .context import Context


@define
class Session:
    conclusions: List[str] = Factory(list)
    failed_trajectories: List[Context] = Factory(list)
    root: Optional[Context] = None
    tools: List[BaseTool] = Factory(list)

    @property
    def id(self):
        return self.root.id()

    def find_tool(self, name: str) -> BaseTool | None:
        for tool in self.tools:
            if tool.name in name:
                return tool
