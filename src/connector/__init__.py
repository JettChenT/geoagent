from typing import List, Optional
from ..context import Context, Message
from ..session import Session


class LMM:
    def prompt(self, context: Context | List[Message], session: Session, stop: Optional[List[str]] = None, n: int = 1, temperature: float|None = None) -> List[Message]:
        pass


    def heartbeat(self) -> bool:
        pass
