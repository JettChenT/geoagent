import os

from streetview import search_panoramas, get_streetview
import dotenv
from PIL import Image
from langchain.tools import tool
import utils
from coords import Coords
import random
import textwrap
PANO_LIMIT = 10

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

@tool("Get StreetViews")
def get_panos(coords_path:str) -> str:
    """
    Gets Google Streetview images of coordinates
    :param coords_path: Path to coordinates
    :return:
    """
    coords = Coords.from_csv(coords_path)
    # print(coords)
    pid_set = set()
    for coord in coords:
        pids = search_panoramas(lat=coord[0], lon=coord[1])
        pid_set = pid_set.union({(x.pano_id, (x.lat, x.lon)) for x in pids})
    # print(pid_set)
    res = "Google Streetview Results \n ------------ \n"
    for (pid, coord) in random.sample(sorted(pid_set), min(len(pid_set), PANO_LIMIT)):
        im = get_streetview(pid, api_key=GOOGLE_MAPS_API_KEY)
        loc = utils.save_img(im, "streetview_res")
        res += textwrap.dedent(f"""\
        Location: {coord}
        Streetview: {utils.image_to_prompt(loc)}
        """)
    return res

if __name__ == '__main__':
    utils.toggle_blackbar()
    print(get_panos("sample/nominatim_query_res0.csv"))