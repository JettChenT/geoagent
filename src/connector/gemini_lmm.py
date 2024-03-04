import re
from typing import List

from . import LMM, Context, Message
from ..session import Session
from .. import utils

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import dotenv


def proc_messages(messages: List[Message], session: Session) -> HumanMessage:
    """
    Process messages from the chat history to a HumanMessage object. Cuz Gemini does not support chat mode yet.
    :param messages:
    :return:
    """
    comb = "".join([m.message for m in messages])
    img_tag_pattern = re.compile(r"<img (.*?)>")
    img_tags = img_tag_pattern.findall(comb)
    blocks = img_tag_pattern.split(comb)
    output = []
    for block in blocks:
        if block == "":
            continue
        if block in img_tags:
            image_object = {
                "type": "image_url",
                "image_url": {
                    "url": utils.proc_image_url(block, session),
                },
            }
            output.append(image_object)
        else:
            output.append({"type": "text", "text": block})
    return HumanMessage(content=output)


class Gemini(LMM):
    def __init__(self, model: str = "gemini-pro-vision", stop: List[str] | None = None):
        dotenv.load_dotenv()
        self.model = ChatGoogleGenerativeAI(model=model)
        self.stop = stop

    def prompt(self, context: Context, stop: List[str] | None = None) -> Message:
        messages = context.messages
        human_message = proc_messages(messages)
        _stop = stop or self.stop
        res = self.model.invoke([human_message], stop=_stop)
        return Message(res.content)


if __name__ == "__main__":
    ctx = Context()
    ctx.add_message(
        Message(
            f"Describe this image in detail: {utils.image_to_prompt('./images/kns.png')}"
        )
    )
    gemini = Gemini()
    print(gemini.prompt(ctx).message)
