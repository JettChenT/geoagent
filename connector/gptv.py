from io import BytesIO

from . import VLLM
import dotenv
import os
from PIL import Image
from pathlib import Path
from openai import OpenAI
import base64
from rich import print

def encode_image(image: Image.Image|Path):
    if isinstance(image, Path):
        img_data = open(image, "rb").read()
    else:
        virtual_file = BytesIO()
        image.save(virtual_file, format="PNG")
        img_data = virtual_file.getvalue()
    return f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"

class Gpt4Vision(VLLM):
    def __init__(self, debug: bool = False, max_tokens: int = 300):
        dotenv.load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_API_BASE"))
        self.messages = []
        self.debug = debug
        self.max_tokens = max_tokens

    def system(self, prompt:str):
        self.messages.append({
            "role": "system",
            "content": prompt
        })

    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        content = [{"type": "text", "text": prompt}]
        if image is not None:
            content.append({"type": "image_url", "image_url": {"url":encode_image(image), "detail":"high"}})
        self.messages.append({
            "role": "user",
            "content": content
        })
        response = self.client.chat.completions.create(
            model = "gpt-4-vision-preview",
            messages = self.messages,
            max_tokens = self.max_tokens
        )
        if self.debug:
            print(response)
        res = response.choices[0]
        self.messages.append({
            "role": "assistant",
            "content": res.message.content
        })
        return res.message.content

if __name__ == '__main__':
    gpt4 = Gpt4Vision(debug=True)
    print(gpt4.prompt("Describe this image in detail.", Path("images/NY.png")))