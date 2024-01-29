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
from openai._types import NOT_GIVEN
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
            api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_API_BASE"),
            timeout=120
        )
        self.debug = debug
        self.max_tokens = max_tokens

    def prompt(self, context: Context | List[Message], stop: List[str] | None = None, n:int = 1, temperature: float|None=None) -> List[Message]:
        """
        Prompt GPT-4 Vision
        :param temperature: temperature of generation
        :param context: the state of the conversation
        :param stop: stop tokens
        :param n: number of responses
        :return: List of messages
        """
        if stop is None:
            stop = NOT_GIVEN
        if temperature is None:
            temperature = NOT_GIVEN
        msg: List[Message] = context.messages if isinstance(context, Context) else context
        messages = proc_messages(msg)
        if self.debug:
            print(
                f"HASH of messages: {hashlib.md5(str(messages).encode()).hexdigest()}"
            )
        choices = []
        for i in range(n):
            cur_msg = msg
            if i > 0:
                cur_msg.append(Message(f"Previously Generated messages: {list(map(lambda x: x.content, choices))}. "
                                       f"Now, generate a different choice:"))
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=proc_messages(cur_msg),
                max_tokens=self.max_tokens,
                stop=stop,
                temperature=temperature,
            )
            if not response.choices:
                print(response)
                raise Exception("No response from GPT-4 Vision")
            r = response.choices[0]
            choices.append(r.message)
        if self.debug:
            print(choices)
        return [Message(c.content, c.role) for c in choices]


if __name__ == "__main__":
    ctx = Context()
    ctx.add_message(
        Message(
            f"Describe this image in a sentence: {utils.image_to_prompt('./datasets/IM2GPS/2k_random_test_anon/4d29d379-d3dc-4266-a559-5e65aac6516d.jpg')}"
        )
    )
    gptv = Gpt4Vision()
    print(gptv.prompt(ctx, n=3))
