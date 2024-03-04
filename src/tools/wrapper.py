from functools import wraps, partial
from typing import Union, Callable, Optional, Type, List
from pydantic import BaseModel
from langchain_core.runnables import Runnable
from langchain.tools import tool, BaseTool
import inspect
from ..session import Session


class GToolWrap:
    def __init__(self, fn: Callable, args, return_direct: bool, args_schema, infer_schema):
        self.fn = fn
        self.args = args
        self.return_direct = return_direct
        self.args_schema = args_schema
        self.infer_schema = infer_schema

    def to_tool(self, session: Session) -> BaseTool:
        f = self.fn
        if 'session' in inspect.signature(f).parameters:
            f = partial(f, session=session)
        if 'ses' in inspect.signature(f).parameters:
            f = partial(f, ses=session)
        return tool(*self.args,
                    return_direct=self.return_direct,
                    args_schema=self.args_schema,
                    infer_schema=self.infer_schema)(f)


def gtool(
        *args: Union[str, Callable, Runnable],
        return_direct: bool = False,
        args_schema: Optional[Type[BaseModel]] = None,
        infer_schema: bool = True,
):
    if len(args) == 1 and callable(args[0]):
        return GToolWrap(args[0], (), return_direct, args_schema, infer_schema)

    def _partial(func: Callable):
        return GToolWrap(func, args, return_direct, args_schema, infer_schema)

    return _partial

def proc_tools(tools: List[BaseTool|GToolWrap], session: Session) -> List[BaseTool]:
    return [t.to_tool(session) if isinstance(t, GToolWrap) else t for t in tools]
