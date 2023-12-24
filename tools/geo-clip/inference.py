from typing import Tuple, List

from PIL import Image
from pathlib import Path
import torch
from langchain.tools import tool

from .model.GeoCLIP import GeoCLIP
import utils
from tools import osm

PAR_DIR = Path(__file__).parent

model = GeoCLIP(gps_gallary_path=PAR_DIR/'model/gps_gallery_100K.csv')
model.eval()

def _predict(image: Image.Image , top_n=5) -> List[Tuple[Tuple[float, float], float]]:
    with torch.no_grad():
        top_pred_gps, top_pred_prob = model.predict(image, top_k=5)

    tops = [(tuple(e.item() for e in top_pred_gps[i]), top_pred_prob[i].item()) for i in range(top_n)]
    return tops

@tool("Geoclip")
def geoclip_predict(img_file) -> str:
    """
    The Geoclip model is an image model that predicts the likely GPS location of an image based on its visual features.
    Feel free to use this as starting point for your investigation.
    :param img_file: the url or location of the image file
    """
    image = utils.load_image(img_file)
    tops = _predict(image)
    viz = osm.render([it[0] for it in tops])
    saved = utils.save_img(viz, 'geoclip')
    cords_fmt = "\n".join([f"lat: {it[0][0]}, lon: {it[0][1]}, prob: {it[1]}" for it in tops])
    return f"""
    GEOCLIP Prediction Results:
    Top 5 likely coordinates:
    {cords_fmt}
    A rendering of those coordinates:
    {utils.image_to_prompt(str(saved))}
    """

if __name__ == "__main__":
    img_path = PAR_DIR/'images/Kauai.png'
    tops = geoclip_predict(str(img_path))
    print(tops)