import re
from markdownify import MarkdownConverter, abstract_inline_conversion
from io import BytesIO
import base64
from PIL import Image


class OAIConverter(MarkdownConverter):
    def convert_code(self, el, text, convert_as_inline):
        classes = el.get("class")
        if classes and "hljs" in classes:
            converter = abstract_inline_conversion(lambda self: "```")
            return converter(self, el, text, convert_as_inline)
        return super().convert_code(el, text, convert_as_inline)


def md(text: str) -> str:
    return OAIConverter(strip=["pre"]).convert(text)


def find_last_code_block(text: str) -> str:
    # Regular expression to match code blocks enclosed within triple backticks
    # The regular expression skips the optional language specifier
    code_blocks = re.findall(r"```(?:[a-zA-Z0-9_+-]*)\n?([\s\S]*?)```", text)

    if code_blocks:
        return code_blocks[-1]
    return None


def image_to_base64(im: Image) -> str:
    buffer = BytesIO()
    im.save(buffer, "PNG")
    buffer.seek(0)
    img_bytes = buffer.read()
    return base64.b64encode(img_bytes).decode("utf-8")
