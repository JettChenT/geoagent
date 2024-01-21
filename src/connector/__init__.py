from typing import List, Optional
from ..context import Context, Message


class LMM:
    def prompt(self, context: Context, stop: Optional[List[str]]) -> Message:
        pass

    def heartbeat(self) -> bool:
        pass
