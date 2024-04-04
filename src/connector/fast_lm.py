# Fast and low-cost llm strategy
# using gpt 3.5 for now

from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai import OpenAI
from openai._types import NOT_GIVEN, NotGiven
from typing import List, Dict
import backoff
from . import LMM
from .. import config
from ..context import Context, Message
from ..session import Session
import os


class Gpt35(LMM):
    def __init__(self, model_name: str = "gpt-3.5-turbo", debug: bool = False):
        self.model_name = model_name
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
        )
        self.debug = debug

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    def _create_completions(self, model: str, messages: List[Dict], max_tokens: int | NotGiven = NOT_GIVEN,
                            stop: List[str] | NotGiven = NOT_GIVEN, temperature: float | NotGiven = NOT_GIVEN,
                            timeout: float | NotGiven = NOT_GIVEN, n: int | NotGiven = NOT_GIVEN) -> ChatCompletion:
        res = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stop=stop,
            temperature=temperature,
            timeout=timeout,
            n=n
        )
        if not res.choices:
            raise Exception("No response from GPT-3.5")
        return res
    
    def prompt(self, context: Context | List[Message], session: Session, n: int=1) -> List[Message]:
        """
        Prompt GPT-3.5
        :param context: the state of the conversation
        :param n: number of responses
        :return: List of messages
        """
        msg: List[Message] = context.messages if isinstance(context, Context) else context
        messages = list(map(lambda x: {
            "role": x.role or "user",
            "content": x.message
        }, msg))
        if self.debug:
            print(messages)
        res = self._create_completions(
            model=self.model_name,
            messages=messages,
            n=n
        )
        return [Message(r.message.content, r.message.role) for r in res.choices]

