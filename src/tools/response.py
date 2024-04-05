import attr
from attr import Factory

@attr.s
class ToolResponse:
    raw: str = attr.ib()
    auxiliary: dict = attr.ib(default=Factory(dict))

