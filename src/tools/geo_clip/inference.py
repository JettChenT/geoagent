from typing import Tuple, List

from PIL import Image
from pathlib import Path
import torch
from langchain.tools import tool
from functools import cache

from .model.GeoCLIP import GeoCLIP
from ... import utils
from ...coords import Coords
from ...session import Session
from ..wrapper import gtool
from ..response import ToolResponse


PAR_DIR = Path(__file__).parent

model = None


def initialize_model():
    global model
    model = GeoCLIP(gps_gallary_path=PAR_DIR / "model/gps_gallery_100K.csv")
    model.eval()


def predict(image: Image.Image, top_n=5) -> List[Tuple[Tuple[float, float], float]]:
    if model is None:
        initialize_model()
    with torch.no_grad():
        top_pred_gps, top_pred_prob = model.predict(image, top_k=5)

    tops = [
        (tuple(e.item() for e in top_pred_gps[i]), top_pred_prob[i].item())
        for i in range(top_n)
    ]
    return tops


@gtool("Geoclip", cached=True)
def geoclip_predict(img_id: str, session: Session) -> ToolResponse:
    """
    The Geoclip model is an image model that predicts the likely GPS location of an image based on its visual features.
    Feel free to use this as starting point for your investigation.
    You can use this tool to find an estimate of the geographical area if you can not find clear hints from the image.
    Note that this model is not perfect and might give you wrong results.
    Prefer using it if the image is landscape or has clear geographical/ cultural features.
    Prefer not to use this in cities or urban areas.
    :param img_id: the image id
    """
    image = utils.load_image(session.get_loc(img_id))
    tops = predict(image)

    cords = Coords([it[0] for it in tops])
    viz = cords.render()
    saved = utils.save_img(viz, "geoclip", session)
    cords_fmt = "\n".join(
        [f"lat: {it[0][0]}, lon: {it[0][1]}, prob: {it[1]}" for it in tops]
    )
    res_pmpt =  f"""
    GEOCLIP Prediction Results:
    Top 5 likely coordinates:
    {cords_fmt}
    A rendering of those coordinates:
    {utils.image_to_prompt(str(saved), session)}
    """
    return ToolResponse(res_pmpt, {"geojson": cords.to_geojson()})


if __name__ == "__main__":
    img_path = PAR_DIR / "images/Kauai.png"
    tops = geoclip_predict(str(img_path))
    print(tops)
