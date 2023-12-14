from pathlib import Path
from PIL import Image

class VLLM:
    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        pass

    def heartbeat(self) -> bool:
        pass

    def system(self, prompt:str):
        self.prompt(prompt)