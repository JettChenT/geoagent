from .auth import GOOGLE_MAPS_API_KEY
from tools.output import debug

from streetview import search_panoramas, get_streetview
from PIL import Image
from langchain.tools import tool
from tqdm import tqdm
import utils
from coords import Coords
import random
import textwrap
PANO_LIMIT = 70

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
def get_panos(coords_path : str) -> str:
    """
    Gets Google Streetview images of coordinates
    :param coords_path: Path to the csv file containing coordinates information
    :return:
    """
    # TODO: pano tiles
    coords = Coords.from_csv(coords_path)
    # print(coords)
    pid_set = set()
    for coord in coords:
        pids = search_panoramas(lat=coord[0], lon=coord[1])
        pid_set = pid_set.union({(x.pano_id, (x.lat, x.lon)) for x in pids})
    # print(pid_set)
    res = "Google Streetview Results \n ------------ \n"
    debug("Getting streetviews...")
    coord_l = []
    auxiliary_l = []
    for (pid, coord) in tqdm(random.sample(sorted(pid_set), min(len(pid_set), PANO_LIMIT))):
        im = get_streetview(pid, api_key=GOOGLE_MAPS_API_KEY)
        loc = utils.save_img(im, "streetview_res")
        res += textwrap.dedent(f"""\
        Location: {coord}
        Streetview: {utils.image_to_prompt(loc)}
        """)
        coord_l.append(coord)
        auxiliary_l.append({"panorama_id": pid, "image_path": loc})
    coords = Coords(coord_l, auxiliary_l)
    res += coords.to_prompt("streetview_")
    return res

if __name__ == '__main__':
    utils.toggle_blackbar()
    print(get_panos("./run/textsearch_coords2.csv"))