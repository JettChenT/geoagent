import os
import time
from typing import List

import torch
from dataclasses import dataclass
from pathlib import Path

from torch import autocast
from tqdm import tqdm
from PIL import Image
from langchain.tools import tool

from torchvision import transforms

from ...coords import Coords
from ...session import Session
from ... import utils
from ..ml import load_image, using_mps, cosine_similarity
from ..wrapper import gtool, ToolResponse
from .sample4geo.model import TimmModel

CUR_PATH = Path(__file__).parent
TOP_N = 15


@dataclass
class Configuration:
    model: str = "convnext_base.fb_in22k_ft_in1k_384"
    img_size: int = 384
    batch_size: int = 128
    verbose: bool = True
    gpu_ids: tuple = (0,)
    normalize_features: bool = True
    data_folder = CUR_PATH / "data/uk1"
    checkpoint_start = (
            CUR_PATH / "pretrained/cvusa/convnext_base.fb_in22k_ft_in1k_384/weights_e40_98.6830.pth"
    )
    num_workers: int = 0 if os.name == "nt" else 4
    device: str = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    neighbour_range: int = 64


def get_model(config):
    model = TimmModel(config.model, pretrained=True, img_size=config.img_size)
    if config.checkpoint_start is not None:
        model_state_dict = torch.load(
            config.checkpoint_start, map_location=torch.device("cpu")
        )
        model.load_state_dict(model_state_dict, strict=False)
    if torch.cuda.device_count() > 1 and len(config.gpu_ids) > 1:
        model = torch.nn.DataParallel(model, device_ids=config.gpu_ids)
    model = model.to(config.device)
    return model


def predict_from_paths(train_config, model, image_paths):
    model.eval()

    preprocess = transforms.Compose([
        transforms.ToTensor(),
    ])

    if train_config.verbose:
        bar = tqdm(image_paths, total=len(image_paths))
    else:
        bar = image_paths

    img_features_list = []

    ids_list = []
    cast_dev = "cuda" if train_config.device == "cuda" else "cpu"
    with torch.no_grad():
        for idx, img_path in enumerate(bar):
            image = Image.open(img_path).convert("RGB")
            image = preprocess(image).unsqueeze(0)  # Add batch dimension

            with autocast(cast_dev):
                image = image.to(train_config.device)
                img_feature = model(image)

                # normalize is calculated in fp32
                if train_config.normalize_features:
                    img_feature = torch.nn.functional.normalize(img_feature, dim=-1)

            # save features in fp32 for sim calculation
            img_features_list.append(img_feature.to(torch.float32))
            ids_list.append(idx)  # Use idx as ID if no other IDs are provided

        # keep Features on GPU
        img_features = torch.cat(img_features_list, dim=0)
        ids_list = torch.tensor(ids_list).to(train_config.device)

    if train_config.verbose:
        bar.close()

    return img_features, ids_list


def loc_sim(target: Path, db: List[Path], config: Configuration):
    model = get_model(config)
    w_target, _ = predict_from_paths(config, model, [target])
    w_db, _ = predict_from_paths(config, model, db)
    s = cosine_similarity(w_target, w_db)
    return s


@gtool("Satellite Locate")
def satellite_locate(img_id: str, db_loc: str, session: Session) -> ToolResponse:
    """
    Locates an image using the satellite database. Must use the satellite tool to download the database first.
    :param img_id: the id of the image to be located
    :param db_loc: the location of a coordinate csv/geojson file whose auxiliary information contains the location to the downloaded satellite images
    Note that db_loc must come from the result of the satellite tool.
    :return:
    """
    db_coords = Coords.load(utils.try_find_loc(session, db_loc, [".geojson", ".csv"]))
    cfig = Configuration()
    res = loc_sim(Path(session.get_loc(img_id)), [Path(x["satellite_imagery"]) for x in db_coords.auxiliary], cfig)
    new_coords = Coords(
        coords=db_coords.coords,
        auxiliary=[
            {"confidence": float(x), "satellite_imagery": y["satellite_imagery"]}
            for (x, y) in zip(res.flatten(), db_coords.auxiliary)
        ],
    )
    top_n = torch.argsort(res, descending=True).flatten()[:TOP_N]
    res = f"Top {TOP_N} possible locations based on visual place recognition: \n"
    for t in range(len(top_n)):
        res += (
            f"Location {t + 1}:\n"
            f"Image: {utils.image_to_prompt(db_coords.auxiliary[top_n[t]]['satellite_imagery'], session)}\n"
            f"Coordinate: {new_coords.coords[top_n[t]]}\n"
        )
    res += f"Full results: \n {new_coords.to_prompt(session, 'satloc_', render=False)}"
    return ToolResponse(res, {
        "geojson": Coords([new_coords.coords[t] for t in top_n]).to_geojson(), 
        "images": [db_coords.auxiliary[t]["satellite_imagery"] for t in top_n]}
    )


if __name__ == '__main__':
    ses = Session()
    t = satellite_locate.to_tool(ses)
    print(t.args)
    args = utils.get_args(t, "./images/anon/7.png, run/0x28ad02390/satellite_coordsc621ea.geojson")
    print(args)
    print(t._run(*args))
