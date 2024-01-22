from typing import List, Optional
from ..context import Context, Message


class LMM:
    def prompt(self, context: Context | List[Message], stop: Optional[List[str]] = None, n: int = 1) -> List[Message]:
        pass


    def heartbeat(self) -> bool:
        pass
