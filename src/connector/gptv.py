import re
from io import BytesIO
from typing import List, Dict, Optional
from enum import Enum
from functools import partial

from langchain_core.messages import HumanMessage
from openai.types.chat import ChatCompletion, ChatCompletionMessage

from .. import utils
from . import LMM, Message, Context
import dotenv
import os
from PIL import Image
from pathlib import Path
from openai import OpenAI
from openai._types import NOT_GIVEN, NotGiven
from rich import print
from ..utils import encode_image, DEBUG_DIR
import hashlib
import backoff


class MultiGenStrategy(Enum):
    SAMPLE = 1
    SEQUENTIAL = 2
    BATCH = 3


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


def _generate_batch(lm, messages: List[Message], n: int) -> List[ChatCompletionMessage]:
    # this should only be used with the ReACT flow
    if n == 1:
        return _generate_sequential(lm, messages, n)
    msg_mod = messages.copy()
    msg_mod.append(Message(f"Please generate {n} different choices."
                           f"For each choice, follow the same format, "
                           f"but with a different potential action that can lead to the result."
                           f"after the `Observation:`."
                           f"Remember to generate only one Thought Action sequence for each choice."
                           f"After generating the Action Input, directly move on to the next choice."
                           f"DO NOT generate 'Observation:' ."
                           f"always move on to the next choice starting with the exact letters `<SEP>` "
                           f"ALWAYS include the exact letters `<SEP>` between each choice."
                           f"After you generated all the choices, "
                           f"ALWAYS include the phrase `<END>` to indicate the end of the choices."
                           f"Remember, <SEP> and <END> are case sensitive."
                           f"Now, generate your choices: "))
    res = lm(messages=proc_messages(msg_mod), stop=["<END>"])
    if not res.choices:
        print(res)
        raise Exception("No response from GPT-4 Vision")
    return list(map(
        lambda x: ChatCompletionMessage(content=x, role="assistant"),
        res.choices[0].message.content.split("<SEP>")
    ))[:n]


def _generate_sample(lm, messages: List[Message], n: int) -> List[ChatCompletionMessage]:
    res = lm(messages=messages, n=n)
    if not res.choices:
        print(res)
        raise Exception("No response from GPT-4 Vision")
    return [r.message for r in res.choices]


def _generate_sequential(lm, messages: List[Message], n: int) -> List[ChatCompletionMessage]:
    choices = []
    for i in range(n):
        cur_msg = messages.copy()
        if i > 0:
            cur_msg.append(Message(f"Previously Generated messages: {list(map(lambda x: x.content, choices))}. "
                                   f"Now, generate a different choice:"))
        response = lm(messages=proc_messages(cur_msg))
        if not response.choices:
            print(response)
            raise Exception("No response from GPT-4 Vision")
        r = response.choices[0]
        choices.append(r.message)
    return choices


class Gpt4Vision(LMM):
    def __init__(self,
                 debug: bool = False,
                 max_tokens: int = 3000,
                 multi_gen_strategy: MultiGenStrategy = MultiGenStrategy.BATCH
                 ):
        dotenv.load_dotenv()
        # Adds black bar containing the location of the image, since gpt-vision api does not recognize image order.
        # utils.toggle_blackbar()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_API_BASE"),
            timeout=360
        )
        self.debug = debug
        self.max_tokens = max_tokens
        self.multi_gen_strategy = multi_gen_strategy

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    def _create_completions(self, model: str, messages: List[Dict], max_tokens: int | NotGiven = NOT_GIVEN,
                            stop: List[str] | NotGiven = NOT_GIVEN, temperature: float | NotGiven = NOT_GIVEN,
                            timeout: float | NotGiven = NOT_GIVEN, n: int | NotGiven = NOT_GIVEN) -> ChatCompletion:
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stop=stop,
            temperature=temperature,
            timeout=timeout,
            n=n
        )

    def prompt(self, context: Context | List[Message], stop: List[str] | NotGiven = NOT_GIVEN, n: int = 1,
               temperature: float | NotGiven = NOT_GIVEN,
               multi_gen_strategy: MultiGenStrategy | None = None) -> List[Message]:
        """
        Prompt GPT-4 Vision
        :param temperature: temperature of generation
        :param context: the state of the conversation
        :param stop: stop tokens
        :param n: number of responses
        :return: List of messages
        """
        multi_gen_strategy = multi_gen_strategy or self.multi_gen_strategy
        msg: List[Message] = context.messages if isinstance(context, Context) else context
        if self.debug and isinstance(context, Context):
            tar_path = DEBUG_DIR / f"{context.digest()}.json"
            context.dump(tar_path)
            print(f"Dumped context to {tar_path}")
        if self.debug:
            print(msg)
        messages = proc_messages(msg)
        if self.debug:
            print(
                f"HASH of messages: {hashlib.md5(str(messages).encode()).hexdigest()}"
            )
        choices = []
        pmpt = partial(self._create_completions,
                       model="gpt-4-vision-preview",
                       max_tokens=self.max_tokens,
                       stop=stop,
                       temperature=temperature,
                       timeout=360
                       )
        match multi_gen_strategy:
            case MultiGenStrategy.SAMPLE:
                choices = _generate_sample(pmpt, msg, n)
            case MultiGenStrategy.SEQUENTIAL:
                choices = _generate_sequential(pmpt, msg, n)
            case MultiGenStrategy.BATCH:
                choices = _generate_batch(pmpt, msg, n)

        if self.debug:
            print(choices)
        return [Message(c.content, c.role) for c in choices]


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    ctx = Context.load(Path("debug/8c046045d9533fc2b6c858c57e71b91c.json"))
    print(str(ctx))
    gptv = Gpt4Vision(debug=True, multi_gen_strategy=MultiGenStrategy.BATCH)
    print(gptv.prompt(ctx, n=3))
