from pathlib import Path
from PIL import Image


class VLLM:
    def prompt(self, prompt: str, image: Image | Path | None = None) -> str:
        pass

    def heartbeat(self) -> bool:
        pass
