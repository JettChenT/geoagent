import re
from pathlib import Path

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


def find_last_code_block(text: str) -> str | None:
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

def encode_image(image: Image.Image | Path, max_size_mb=2):
    # Open the image from a file path if it's not already an Image object
    if isinstance(image, Path):
        image = Image.open(image)

    if image.mode == 'RGBA':
        image = image.convert('RGB')
    # Convert max_size_mb to bytes
    max_encoded_size_bytes = (max_size_mb * 1024 * 1024) * 3 / 4 if max_size_mb else None

    # Initial setup for quality
    quality = 100
    virtual_file = BytesIO()

    while True:
        virtual_file.seek(0)
        virtual_file.truncate()
        image.save(virtual_file, format="JPEG", quality=quality)
        img_data = virtual_file.getvalue()
        encoded_data = base64.b64encode(img_data).decode('utf-8')

        # Check if the encoded data size is within the specified limit
        if max_encoded_size_bytes is None or len(encoded_data) <= max_encoded_size_bytes:
            break

        # If not, decrease quality
        quality -= 5
        if quality <= 10:  # Prevent the quality from becoming too low
            break

    return f"data:image/jpeg;base64,{encoded_data}"