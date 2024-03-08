import os
import torch
import numpy as np
from PIL import Image
from typing import List
import torchvision.transforms as transforms
from pathlib import Path
from langchain.tools import tool

from ...coords import Coords
from ... import utils
from ..ml import using_mps, load_image, cosine_similarity
from ..wrapper import gtool, Session

model = None
TOP_N = 15
base_transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def get_model():
    global model
    if model is not None:
        return model
    model = torch.hub.load(
        "gmberton/eigenplaces",
        "get_trained_model",
        backbone="ResNet50",
        fc_output_dim=2048,
    )
    if using_mps():
        mps_device = torch.device("mps")
        model.to(mps_device)
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


def loc_sim(target: Image.Image, db: List[Image.Image]):
    w_target = weight_im(target)
    w_db = weight_im(db)
    print(w_target.shape, w_db.shape)
    s = cosine_similarity(w_target, w_db)
    return s

@gtool("Streetview Locate")
def locate_image(img_id: str, db_loc: str, session: Session):
    """
    Locates an image using the streetview database. Must use the streetview tool to download the database first.
    :param img_id: the id of the image to be located
    :param db_loc: the location of a coordinate csv/geojson file whose auxiliary information contains the location to the downloaded streetview images
    Note that db_loc must come from the result of the streetview tool.
    :return:
    """
    db_coords = Coords.load(db_loc)
    im = load_image(session.get_loc(img_id))
    res = loc_sim(im, [load_image(x["image_path"]) for x in db_coords.auxiliary])
    new_coords = Coords(
        coords=db_coords.coords,
        auxiliary=[
            {"confidence": float(x), "image_path": y["image_path"]}
            for (x, y) in zip(res.flatten(), db_coords.auxiliary)
        ],
    )
    top_n = torch.argsort(res, descending=True).flatten()[:TOP_N]
    res = f"Top {TOP_N} possible locations based on visual place recognition: \n"
    for t in range(TOP_N):
        res += (
            f"Location {t+1}:\n"
            f"Image: {utils.image_to_prompt(db_coords.auxiliary[top_n[t]]['image_path'], session)}\n"
            f"Coordinate: {new_coords.coords[top_n[t]]}\n"
        )
    res += f"Full results: \n {new_coords.to_prompt(session, 'vpr_', render=False)}"
    return res


if __name__ == "__main__":
    # res = loc_sim(
    #     load_image('./tools/vpr/ds/query.png'),
    #     [load_image(f'./bak/run_svst/streetview_res{i}.png') for i in range(70)]
    # )
    # print(list(enumerate(res)))
    # print(torch.argsort(res))
    print(locate_image._run("./images/anon/5.png", "./run/streetview_coords0.csv"))
