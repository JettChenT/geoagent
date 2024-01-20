import os
import torch
import numpy as np
from PIL import Image
from typing import List
import torchvision.transforms as transforms
from pathlib import Path
from langchain.tools import tool
from .mixvpr import get_mixvpr

from coords import Coords
import utils

model = None
TOP_N = 15
base_transform = transforms.Compose([
            transforms.ToTensor(),
        ])

def using_mps():
    return torch.backends.mps.is_available() and torch.backends.mps.is_built() and os.environ.get("USE_MPS", "0") == "1"

def load_image(loc: str|Path):
    return Image.open(loc).convert("RGB")

def get_model():
    global model
    if model is not None:
        return model
    model = get_mixvpr(4096)
    return model

def weight_im(im: Image.Image | List[Image.Image]):
    mod = get_model()
    if not isinstance(im, list):
        im = [im]
    input_tensor = torch.stack([base_transform(i) for i in im])
    if using_mps():
        mps_device = torch.device("mps")
        input_tensor = input_tensor.to(mps_device)
    output = mod(input_tensor)
    return output

def cosine_similarity(vec1: torch.Tensor, vec2: torch.Tensor) -> torch.Tensor:
    dot_product = vec1 @ vec2.T
    norm_vec1 = torch.norm(vec1)
    norm_vec2 = torch.norm(vec2, dim=1)
    similarity = dot_product / (norm_vec1 * norm_vec2)
    return similarity

def loc_sim(target: Image.Image, db: List[Image.Image]):
    w_target = weight_im(target)
    w_db = weight_im(db)
    print(w_target.shape, w_db.shape)
    s = cosine_similarity(w_target, w_db)
    return s

@tool("Streetview Locate")
def locate_image(im_loc: str, db_loc:str):
    """
    Locates an image using the streetview database. Must use the streetview tool to download the database first.
    :param im_loc: the location of the image to be located
    :param db_loc: the location of a coordinate csv file whose auxiliary information contains the location to the downloaded streetview images
    :return:
    """
    db_coords = Coords.from_csv(db_loc)
    im = load_image(im_loc)
    res = loc_sim(im, [load_image(x['image_path']) for x in db_coords.auxiliary])
    new_coords = Coords(
        coords = db_coords.coords,
        auxiliary = [{"confidence": float(x), 'image_path': y['image_path']} for (x,y) in zip(res.flatten(), db_coords.auxiliary)]
    )
    top_n = torch.argsort(res).flatten()[:TOP_N]
    res = f"Top {TOP_N} possible locations based on visual place recognition: \n"
    for t in range(TOP_N):
        res += (f"Location {t+1}:\n"
                f"Image: {utils.image_to_prompt(db_coords.auxiliary[top_n[t]]['image_path'])}\n"
                f"Coordinate: {new_coords.coords[top_n[t]]}\n")
    res += f"Full results: \n {new_coords.to_prompt('vpr_', render=False)}"
    return res

if __name__ == '__main__':
    # res = loc_sim(
    #     load_image('./tools/vpr/ds/query.png'),
    #     [load_image(f'./bak/run_svst/streetview_res{i}.png') for i in range(70)]
    # )
    # print(list(enumerate(res)))
    # print(torch.argsort(res))
    print(locate_image._run('./images/anon/5.png', './run/streetview_coords0.csv'))
