from .auth import GOOGLE_MAPS_API_KEY
from ...coords import Coords
from PIL import Image
import io
from functools import cache
from ... import utils
from langchain.tools import tool

import requests

AUTH_HEAD = {"Content-Type": "application/json", "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY}


def wrap_auth(head):
    return dict(head, **AUTH_HEAD)


@tool
@cache
def text_search(query: str):
    """
    Returns information about a location based on a text query. Uses Google Places API.
    This is equivalent to a Google Maps search.
    The CSV file returned would contain the coordinates of the location, as well as auxiliary information about the location, including
    the name, address, and photo ids.
    :param query: the text query
    :return:
    """
    # TODO: dump result into a json
    r = requests.post(
        "https://places.googleapis.com/v1/places:searchText",
        json={"textQuery": query},
        headers=wrap_auth(
            {
                "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.photos"
            }
        ),
    )
    res_data = r.json()
    if 'places' not in res_data:
        print(res_data)
        return f"Invalid response: {res_data}"
    res_data_disp = [
        {"name": x["displayName"]["text"], "location": x["location"]}
        for x in res_data["places"]
    ]
    res_coords = Coords(
        [
            (x["location"]["latitude"], x["location"]["longitude"])
            for x in res_data["places"]
        ],
        res_data["places"],
    )
    return f"Results for query: {res_data_disp}\n Coordinates: {res_coords.to_prompt('textsearch_')}"


SATELLITE_CAP = 125
TOP_N = 15


@tool
def plot_satellite(coords_loc: str):
    """
    Plots the satellite image of a given set of coordinates. Uses Google Maps Static API.
    :param coords_loc: the location of the coordinate csv file
    :return:
    """
    coords = Coords.load(coords_loc)
    if len(coords) > SATELLITE_CAP:
        return f"Too many coordinates: {len(coords)} > {SATELLITE_CAP}"
    retrieved = []
    for coord in coords:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/staticmap",
            params={
                "center": f"{coord[0]},{coord[1]}",
                "zoom": 19,
                "size": "640x640",
                "maptype": "satellite",
                "key": GOOGLE_MAPS_API_KEY,
            },
        )
        im = Image.open(io.BytesIO(r.content))
        loc = utils.save_img(im, "satellite_res")
        retrieved.append((coord, loc))
    sim = "".join(
        [f"{coord}: {utils.image_to_prompt(loc)}\n" for (coord, loc) in retrieved[:TOP_N]]
    )
    full_res = Coords(
        coords=[x[0] for x in retrieved],
        auxiliary=[{"satellite_imagery": str(x[1])} for x in retrieved],
    )
    return f"""
    Satellite Images({len(retrieved)} available, showing top {len(sim)}):
    {sim}
    Full Results:
    {full_res.to_prompt('satellite_', render=False)}
    """


if __name__ == "__main__":
    from rich import print

    print(plot_satellite("./run/textsearch_coordse8dd97.geojson"))
