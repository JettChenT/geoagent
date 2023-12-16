import os

from streetview import search_panoramas, get_streetview
import dotenv
from PIL import Image
from langchain.tools import tool
# TODO: support multimodal tool returns, and make this a tool.

dotenv.load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_pano(lat: float, lon: float) -> str | Image.Image:
    """
    Gets the panorama id for a given lat, lon pair.
    :param lat:
    :param lon:
    :return:
    """
    res = search_panoramas(lat=lat, lon=lon)
    if len(res) == 0:
        return "No panoramas found for this location."
    pid = res[0].pano_id
    return get_streetview(pid, api_key=GOOGLE_MAPS_API_KEY)

if __name__ == '__main__':
    get_pano(40.714728, -73.998672).show()