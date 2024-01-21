import re
from io import BytesIO
from typing import List, Dict, Optional

from langchain_core.messages import HumanMessage

from .. import utils
from . import LMM, Message, Context
import dotenv
import os
from PIL import Image
from pathlib import Path
from openai import OpenAI
from rich import print
from ..utils import encode_image
import hashlib


def proc_messages(messages: List[Message]) -> List[Dict]:
    """
    Process messages from the chat history to a HumanMessage object. Cuz Gemini does not support chat mode yet.
    :param messages:
    :return:
    """
    img_tag_pattern = re.compile(r"<img (.*?)>")
    res = []
    for message in messages:
        m = message.message
        img_tags = img_tag_pattern.findall(m)
        blocks = img_tag_pattern.split(m)
        output = []
        for block in blocks:
            if block == "":
                continue
            if block in img_tags:
                image_object = {
                    "type": "image_url",
                    "image_url": {"url": utils.proc_image_url(block)},
                }
                output.append(image_object)
            else:
                output.append({"type": "text", "text": block})
        res.append({"role": message.role or "user", "content": output})
    return res


class Gpt4Vision(LMM):
    def __init__(self, debug: bool = False, max_tokens: int = 3000):
        dotenv.load_dotenv()
        # Adds black bar containing the location of the image, since gpt-vision api does not recognize image order.
        # utils.toggle_blackbar()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_API_BASE")
        )
        self.debug = debug
        self.max_tokens = max_tokens

    def prompt(self, context: Context, stop: Optional[List[str]]) -> Message:
        messages = proc_messages(context.messages)
        if self.debug:
            print(
                f"HASH of messages: {hashlib.md5(str(messages).encode()).hexdigest()}"
            )
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=self.max_tokens,
            stop=stop,
        )
        if self.debug:
            print(response)
        if not response.choices:
            print(response)
            raise Exception("No response from GPT-4 Vision")
        res_msg = response.choices[0].message
        return Message(res_msg.content, res_msg.role)


if __name__ == "__main__":
    ctx = Context()
    ctx.add_message(
        Message(
            f"Describe this image in detail: {utils.image_to_prompt('./images/kns.png')}"
        )
    )
    gptv = Gpt4Vision()
    print(gptv.prompt(ctx).message)
