from .auth import GOOGLE_MAPS_API_KEY
from ...tools.output import debug

from streetview import search_panoramas, get_streetview
from functools import cache
from PIL import Image
from langchain.tools import tool
from tqdm import tqdm
from ... import utils
from ...coords import Coords
import random
import textwrap

PANO_LIMIT = 120
PANO_VIEW_LIMIT = 15


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
@cache
def get_panos(coords_path: str) -> str:
    """
    Gets Google Streetview images of coordinates
    :param coords_path: Path to the csv or geojson file containing coordinates information
    :return:
    """
    # TODO: pano tiles
    # Note: the sampling of streetview images could perhaps be improved in the future. Now it's just a SRS
    # e.g. ensure that each coordinate is represented, and that the coordinates are not too close to each other.
    coords = Coords.load(coords_path)
    print(coords)
    pid_set = set()
    for coord in coords:
        pids = search_panoramas(lat=coord[0], lon=coord[1])
        pid_set = pid_set.union({(x.pano_id, (x.lat, x.lon)) for x in pids})

    if len(pid_set) == 0:
        return "No panoramas found for this location."

    # print(pid_set)
    res = "Google Streetview Results \n ------------ \n"
    debug("Getting streetviews...")
    coord_l = []
    auxiliary_l = []
    sample_previews = []
    for pid, coord in tqdm(
        random.sample(sorted(pid_set), min(len(pid_set), PANO_LIMIT))
    ):
        im = get_streetview(pid, api_key=GOOGLE_MAPS_API_KEY)
        loc = utils.save_img(im, "streetview_res")
        sample_previews.append(
            textwrap.dedent(
                f"""\
        Location: {coord}
        Streetview: {utils.image_to_prompt(loc)}
        """
            )
        )
        coord_l.append(coord)
        auxiliary_l.append({"panorama_id": pid, "image_path": str(loc)})

    for sample in random.sample(
        sample_previews, min(len(sample_previews), PANO_VIEW_LIMIT)
    ):
        res += sample + "\n"
    if len(sample_previews) > PANO_VIEW_LIMIT:
        res += (
            f"{len(sample_previews) - PANO_VIEW_LIMIT} more results not shown. \n"
            f"If the location can not be confirmed or you need to further narrow down the results,"
            f"highly recommend using the `Streetview Locate` tool."
        )

    coords = Coords(coord_l, auxiliary_l)
    res += coords.to_prompt("streetview_")
    return res


if __name__ == "__main__":
    import sys
    utils.toggle_blackbar()
    print(get_panos(sys.argv[1] if len(sys.argv)>1 else "./bak/run_svst/textsearch_coords2.csv"))
