import re
from pathlib import Path

from markdownify import MarkdownConverter, abstract_inline_conversion
from io import BytesIO
import base64
from PIL import Image
import requests

RUN_DIR = 'run/'

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

def image_to_prompt(loc: str):
    """
    Convert an image to its corresponding prompt representation
    :param loc: URL or path to the image
    :return:
    """
    return f"Image {loc}: \n <img {loc}>"

def proc_image_url(url:str) -> str:
    if url.startswith("http"):
        return url
    return encode_image(Path(url))

def load_image(url: str) -> Image.Image:
    if url.startswith("http"):
        return Image.open(BytesIO(requests.get(url).content))
    return Image.open(url)

def find_valid_loc(prefix:str, postfix:str) -> Path:
    """
    Find the first valid location that exists
    """
    for i in range(100):
        path = prefix + str(i) + postfix
        if not Path(path).exists():
            return Path(path)
    raise FileNotFoundError("Could not find any valid location")

def make_run_dir():
    Path(RUN_DIR).mkdir(parents=True, exist_ok=True)

def flush_run_dir():
    Path(RUN_DIR).rmdir()

def save_img(im: Image.Image, ident: str) -> Path:
    """
    Save an image to a file
    """
    make_run_dir()
    p = find_valid_loc(RUN_DIR+ident, ".png")
    im.save(p)
    return p