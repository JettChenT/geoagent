from overpy import Overpass
from typing import List, Tuple, Any
import folium
from ... import prompting
import io
from PIL import Image
import statistics
from langchain.tools import tool
from ... import utils
from ...utils import encode_image
import requests
from ...coords import Coords

overpass = Overpass()
STDEV_THRESHOLD = 0.001


def proc_output(output: str, img: Image.Image | None) -> Any:
    content = [{"type": "text", "text": output}]
    if img is not None:
        content.append({"type": "image_url", "image_url": encode_image(img)})
    return content


def refine_prompt(original, problem) -> str:
    return f"""
    Original Query: ```{original}````
    Problem: ```{problem}```
    Please refine your query to fix the problem.
    """


def refine_query(original, problem) -> str:
    prompt = refine_prompt(original, problem)
    r = requests.post(
        "https://aapi.tech-demos.de/overpassnl/overpassnl", json={"usertext": prompt}
    )
    if r.status_code != 200:
        return (
            f"Something went wrong with overpass query: {r.content}. Please try again."
        )
    return r.json()["osmquery"]


def nl_query(q: str, dep: int = 0, thresh: int = 10, debug: bool = True):
    if debug:
        print(
            f"""
        ----------
        depth: {dep}
        OSM LM Query:
        {q},
        -----------
        """
        )
    osm_query = requests.post(
        "https://aapi.tech-demos.de/overpassnl/overpassnl", json={"usertext": q}
    ).json()["osmquery"]
    try:
        osm_result = overpass.query(osm_query)
        return osm_result
    except Exception as e:
        if dep > thresh:
            return str(e)
        return nl_query(refine_prompt(osm_query, str(e)), dep + 1, thresh, debug)


def _query(q: str, nl: bool = True) -> Tuple[str | Coords, Image.Image | None]:
    try:
        osm_result = (
            nl_query(f"{q}\n Please use regex and loose names when possible.")
            if nl
            else overpass.query(q)
        )
        coords = Coords(
            list(map(lambda x: (float(x.lat), float(x.lon)), osm_result.nodes))
        )
        x_cords, y_cords = coords.split_latlon()
        if len(coords) == 0:
            return prompting.DELTA_TOO_LITTLE, None
        if len(coords) > 1:
            x_std = statistics.stdev(x_cords)
            y_std = statistics.stdev(y_cords)
            # if x_std > STDEV_THRESHOLD or y_std > STDEV_THRESHOLD:
            #     return prompting.TOO_SPREAD, render(coords)
        return coords, coords.render()
    except Exception as e:
        print(e)
        return str(e) + "\n Please Adjust the OSM query to fix this issue.", None


@tool("Overpass Turbo")
def query(q: str) -> Any:
    """
    Queries the Open Streetmap database based on natural language, and return the resulting lat long pairs
    Use this tool to pinpoint locations on the map. Be specific about your conditions.
    :param q: the query you have in natural language. Example: Building whose name contains ... next to ... street in city ...
    :return: list of tuples if valid, otherwise returns a string representing the next prompt
    """
    res, img = _query(q)
    rsp = f"OSM Query result: {res}"
    if isinstance(res, Coords):
        dump_loc = utils.find_valid_loc("osm_query_coords", ".geojson")
        res.to_geojson(dump_loc)
        rsp += f"\n The coordinates are stored at {dump_loc}"
    if isinstance(img, Image.Image):
        loc = utils.save_img(img, "osm_query_res")
        rsp += (
            "\n Here's a A visualization of the OSM results:"
            + utils.image_to_prompt(str(loc))
        )
    return rsp


@tool("Return Coordinates", return_direct=True)
def show_coords(coords: str):
    """
    Use this when you are certain about the coordinates you want to show on the map.
    This returns the results to the end user as the conclusion to your investigation.
    Eg. [(-122.123, 45.123), (-122.123, 45.123)]
    If there are multiple coordinates but they are all pretty close to each other, that's fine.
    But try not to use this tool if the coordinates are too spread out.
    :param coords: (lat, lon) or [(lat, lon)...]
    :return:
    """
    print("RESULT COORDS:", coords)


if __name__ == "__main__":
    QUERY = (
        "Find me a restaurant named Korean Steak House in Washington next to Monroe St"
    )
    print("querying...")
    q_res = query(QUERY)
    print("query result:", q_res)
