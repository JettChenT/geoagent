import io
import shutil
from pathlib import Path
import os
from io import BytesIO
from typing import List

import base64
from PIL import Image, ImageDraw, ImageFont
from langchain.tools import BaseTool
import requests
import sys
from uuid import uuid4
import random
import inspect

from .session import Session

# Mutable Global Variable: Whether to render a black bar at the bottom with the location of image
GLOB_RENDER_BLACKBAR = False
RUN_DIR = "run/"
DEBUG_DIR = Path("./debug")


def image_to_base64(im: Image) -> str:
    buffer = BytesIO()
    im.save(buffer, "PNG")
    buffer.seek(0)
    img_bytes = buffer.read()
    return base64.b64encode(img_bytes).decode("utf-8")


def encode_image(image: Image.Image | Path, max_size_mb=20):
    # Open the image from a file path if it's not already an Image object
    if isinstance(image, Path):
        im = Image.open(image)
        if GLOB_RENDER_BLACKBAR:
            image = render_text_description(im, str(image))

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
    return f"[Image location : {loc}] <img {loc}>"


im_cache = {}


def proc_image_url(url: str, session: Session) -> str:
    if url.startswith("http"):
        return url
    global im_cache
    if url in im_cache:
        return im_cache[url]
    match os.getenv("UPLOAD_IMAGE_USE"):
        case 'gcp' | 'upload':
            res = upload_image(session, Path(url))
        case _:
            res = encode_image(Path(url))
    im_cache[url] = res
    return res


def load_image(url: str) -> Image.Image:
    if url.startswith("http"):
        return Image.open(BytesIO(requests.get(url).content))
    return Image.open(url)


def find_valid_loc(session: Session, prefix: str, postfix: str) -> Path:
    """
    Find the first valid location that exists
    """
    pre_dir = Path(RUN_DIR) / session.id
    for i in range(100_000_000):
        k = random.randbytes(4).hex()[2:]
        path = pre_dir / (prefix + k + postfix)
        if not Path(path).exists():
            return Path(path)
    raise FileNotFoundError("Could not find any valid location")


def make_run_dir(session: Session):
    (Path(RUN_DIR) / session.id).mkdir(parents=True, exist_ok=True)


def flush_run_dir(session: Session):
    # remove everything in RUN_DIR
    shutil.rmtree(Path(RUN_DIR) / session.id, ignore_errors=True)
    make_run_dir(session)


def save_img(im: Image.Image, ident: str, session: Session) -> Path:
    """
    Save an image to a file
    """
    make_run_dir(session)
    p = find_valid_loc(session, ident, ".png")
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
    keys = inspect.signature(tool.func).parameters.keys()
    if len(keys) - list(keys).count("session") <= 1:
        return [tool_input]
    return tool_input.split(", ")


def upload_image(session: Session, image: Path) -> str:
    """
    Upload an image to cloud(sxcu.net) and return the url.
    If the image is not a PNG, it is converted to PNG before upload.
    """
    img = Image.open(image)
    if GLOB_RENDER_BLACKBAR:
        img = render_text_description(img, str(image))
    if os.getenv("UPLOAD_IMAGE_USE") == 'gcp':
        from .tools.gcp import storage as gcp_storage
        tmp_path = find_valid_loc(session, "tmp", ".png")
        img.save(tmp_path)
        return gcp_storage.upload_file(tmp_path, destination_blob_name=f"{str(image)}{uuid4()}.png")
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
    ses = Session()
    print(upload_image(ses, Path("./images/anon/ukr_citycenter.jpg")))
