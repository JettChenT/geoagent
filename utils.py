import re
from markdownify import MarkdownConverter, abstract_inline_conversion


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
