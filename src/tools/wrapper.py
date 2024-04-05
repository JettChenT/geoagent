import functools
import pydoc
from functools import wraps, partial
from typing import Union, Callable, Optional, Type, List
from pydantic import BaseModel
from langchain_core.runnables import Runnable
from langchain.tools import tool, BaseTool
import agentops
import inspect

from .response import ToolResponse
from ..session import Session


class GToolWrap:
    def __init__(self, fn: Callable, args, return_direct: bool, args_schema, infer_schema, cached: bool, use_agentops: bool = False):
        self.fn = fn
        self.args = args
        self.return_direct = return_direct
        self.args_schema = args_schema
        self.infer_schema = infer_schema
        self.cached = cached
        self.use_agentops = use_agentops

    def to_tool(self, session: Session) -> BaseTool:
        f = self.fn
        f_mod = f
        sig = inspect.signature(f)
        if 'session' in inspect.signature(f).parameters:
            np = dict(sig.parameters)
            np.pop("session")
            sig = sig.replace(parameters=list(np.values()))
            f_bak = f
            @functools.wraps(f)
            def g(*args, **kwargs):
                print("ARGS", args, kwargs)
                new_args = sig.bind(*args, **kwargs)
                new_args.apply_defaults()
                all_kwargs = new_args.arguments
                all_kwargs.update(all_kwargs.pop("kwargs", {}))
                all_kwargs["session"] = session
                return f_bak(**all_kwargs)
            f_mod = g
        
        f_mod_bak = f_mod
        @functools.wraps(f)
        def g(*args, **kwargs):
            res = f_mod_bak(*args, **kwargs)
            if isinstance(res, ToolResponse):
                return res
            return ToolResponse(str(res), {})

        f_mod = g

        if self.cached:
            f_mod = functools.cache(f_mod)
        if self.use_agentops:
            f_mod = agentops.record_function(f.__name__)(f_mod)
        f = f_mod
        t: BaseTool = tool(*self.args,
                    return_direct=self.return_direct,
                    args_schema=self.args_schema,
                    infer_schema=self.infer_schema)(f)
        name = f.__name__
        doc = f.__doc__
        t.description = f"{name}{sig} - {doc.strip()}"
        return t

def gtool(
        *args: Union[str, Callable, Runnable],
        return_direct: bool = False,
        args_schema: Optional[Type[BaseModel]] = None,
        infer_schema: bool = False,
        cached: bool = False,
        use_agentops: bool = False
):
    if len(args) == 1 and callable(args[0]):
        return GToolWrap(args[0], (), return_direct, args_schema, infer_schema, cached, use_agentops)

    def _partial(func: Callable):
        return GToolWrap(func, args, return_direct, args_schema, infer_schema, cached, use_agentops)

    return _partial

def proc_tools(tools: List[GToolWrap], session: Session) -> List[BaseTool]:
    return [t.to_tool(session) for t in tools]
