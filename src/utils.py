import io
import re
from pathlib import Path
import os
from io import BytesIO
from typing import List

from markdownify import MarkdownConverter, abstract_inline_conversion
import base64
from PIL import Image, ImageDraw, ImageFont
from langchain.tools import BaseTool
import requests
import sys
from uuid import uuid4
import random

# Mutable Global Variable: Whether to render a black bar at the bottom with the location of image
GLOB_RENDER_BLACKBAR = False
RUN_DIR = "run/"
DEBUG_DIR = Path("./debug")


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


def encode_image(image: Image.Image | Path, max_size_mb=20):
    # Open the image from a file path if it's not already an Image object
    if isinstance(image, Path):
        raw = open(image, "rb").read()
        if max_size_mb is None or sys.getsizeof(raw) / (1e6) <= max_size_mb:
            encoded_img = base64.b64encode(raw).decode("utf-8")
            img_type = "png" if image.suffix == ".png" else "jpeg"
            return f"data:image/{img_type};base64,{encoded_img}"
        image = Image.open(image)

    if image.mode != "RGB":
        image = image.convert("RGB")
    # Convert max_size_mb to bytes
    max_encoded_size_bytes = (
        (max_size_mb * 1024 * 1024) * 3 / 4 if max_size_mb else None
    )

    # Initial setup for quality
    quality = 100

    while True:
        virtual_file = BytesIO()
        image.save(virtual_file, format="JPEG", quality=quality)
        img_data = virtual_file.getvalue()
        encoded_data = base64.b64encode(img_data).decode("utf-8")

        # Check if the encoded data size is within the specified limit
        if (
            max_encoded_size_bytes is None
            or len(encoded_data) <= max_encoded_size_bytes
        ):
            break
        # If not, decrease quality
        print("compressing image")
        quality -= 5
        if quality <= 10:  # Prevent the quality from becoming too low
            break

    return f"data:image/jpeg;base64,{encoded_data}"


def read_image(image: Image.Image | Path, size_mb=0.9):
    if isinstance(image, Path):
        orig_path = image
        image = Image.open(image)
        if GLOB_RENDER_BLACKBAR:
            image = render_text_description(image, str(orig_path))

    if image.mode == "RGBA":
        image = image.convert("RGB")
    # Initial setup for quality
    quality = 100
    virtual_file = BytesIO()

    while True:
        virtual_file.seek(0)
        virtual_file.truncate()
        image.save(virtual_file, format="JPEG", quality=quality)
        img_data = virtual_file.getvalue()
        if size_mb is None or sys.getsizeof(img_data) / (1e6) <= size_mb:
            break

        # If not, decrease quality
        quality -= 5
        if quality <= 10:  # Prevent the quality from becoming too low
            break

    print(f"Image size: {sys.getsizeof(img_data) / (1e6)} MB")
    return img_data


def image_to_prompt(loc: str | Path):
    """
    Convert an image to its corresponding prompt representation
    :param loc: URL or path to the image
    :return:
    """
    if isinstance(loc, Path):
        loc = str(loc)
    return f"Image {loc}: <img {loc}>"


im_cache = {}
def proc_image_url(url: str) -> str:
    if url.startswith("http"):
        return url
    global im_cache
    if url in im_cache:
        return im_cache[url]
    match os.getenv("UPLOAD_IMAGE_USE"):
        case 'gcp' | 'upload':
            res = upload_image(Path(url))
        case _:
            res = encode_image(Path(url))
    im_cache[url] = res
    return res


def load_image(url: str) -> Image.Image:
    if url.startswith("http"):
        return Image.open(BytesIO(requests.get(url).content))
    return Image.open(url)


def find_valid_loc(prefix: str, postfix: str, pre_dir: str = RUN_DIR) -> Path:
    """
    Find the first valid location that exists
    """
    for i in range(100_000_000):
        k = random.randbytes(4).hex()[2:]
        path = pre_dir + prefix + k + postfix
        if not Path(path).exists():
            return Path(path)
    raise FileNotFoundError("Could not find any valid location")


def make_run_dir():
    Path(RUN_DIR).mkdir(parents=True, exist_ok=True)


def flush_run_dir():
    # remove everything in RUN_DIR
    os.system(f"rm -rf {RUN_DIR}")
    make_run_dir()


def save_img(im: Image.Image, ident: str) -> Path:
    """
    Save an image to a file
    """
    make_run_dir()
    p = find_valid_loc(ident, ".png")
    im.save(p)
    return p


def render_text_description(
    image: Image.Image, text: str, line_height=16
) -> Image.Image:
    """
    Render a text description at the bottom of an image. Assumes that text is single line.
    """
    # Create a new image with a black background
    bar = Image.new("RGB", (image.width, int(line_height * 1.2)), "black")

    # Create a draw object and add text to the bar
    draw = ImageDraw.Draw(bar)
    font = ImageFont.truetype("./fonts/Inter-Regular.ttf", line_height)
    text_width = draw.textlength(text, font)
    position = ((bar.width - text_width) / 2, int(line_height * 0.1))
    draw.text(position, text, fill="white", font=font)

    # Concatenate the original image with the bar
    image_with_bar = Image.new("RGB", (image.width, image.height + bar.height))
    image_with_bar.paste(image, (0, 0))
    image_with_bar.paste(bar, (0, image.height))

    return image_with_bar


def toggle_blackbar(to: bool = True):
    global GLOB_RENDER_BLACKBAR
    GLOB_RENDER_BLACKBAR = to


def sanitize(s: str) -> str:
    return (
        s.replace("\n", " ")
        .replace("\t", " ")
        .replace("\r", " ")
        .replace("\\n", "")
        .replace('"', "")
        .strip()
    )


def get_args(tool: BaseTool, tool_input: str) -> List[str]:
    if len(tool.args.keys()) <= 1:
        return [tool_input]
    return tool_input.split(", ")


def upload_image(image: Path) -> str:
    """
    Upload an image to cloud(sxcu.net) and return the url.
    If the image is not a PNG, it is converted to PNG before upload.
    """
    if os.getenv("UPLOAD_IMAGE_USE") == 'gcp':
        from .tools.gcp import storage as gcp_storage
        return gcp_storage.upload_file(image, destination_blob_name=f"{str(image)}{uuid4()}.png")
    img = Image.open(image)
    if image.suffix != ".png":
        png_image_io = io.BytesIO()
        img.save(png_image_io, format="PNG")
        png_image_io.seek(0)
        file_data = {"file": ("image.png", png_image_io, 'image/png')}
    else:
        file_data = {"file": open(image, "rb")}

    res = requests.post(
        "https://sxcu.net/api/files/create", files=file_data
    )
    res.raise_for_status()
    return f"{res.json()['url']}.png"


if __name__ == "__main__":
    print(upload_image(Path("./images/anon/ukr_citycenter.jpg")))
