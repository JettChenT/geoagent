from typing import Callable
from .session import Session
from .context import Message


class ProxiedMessage(Message):
    def __init__(self, msg_fn: Callable[[Session], str], ses: Session, role: str | None = None):
        self.msg_fn = msg_fn
        self.role = role
        self.session = ses

    @property
    def message(self):
        return self.msg_fn(self.session)
