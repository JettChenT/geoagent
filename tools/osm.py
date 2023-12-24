from overpy import Overpass
from typing import List, Tuple, Any
import folium
import prompting
import io
from PIL import Image
import statistics
from langchain.tools import tool
import utils
from utils import encode_image
import requests

PADDING = 0.001
overpass = Overpass()
STDEV_THRESHOLD = 0.001


def proc_output(output: str, img: Image.Image | None) -> Any:
    content = [{"type": "text", "text": output}]
    if img is not None:
        content.append({"type": "image_url", "image_url": encode_image(img)})
    return content

def render(coords: List[Tuple[float, float]]) -> Image.Image:
    """
    Visualizes the coordinates on a map
    :param coords:
    :return:
    """
    x_cords = list(map(lambda x: x[0], coords))
    y_cords = list(map(lambda x: x[1], coords))
    bbox = [[min(x_cords), min(y_cords)], [max(x_cords), max(y_cords)]]
    m = folium.Map()
    m.fit_bounds(bbox, padding=[PADDING] * 4)
    for coord in coords:
        folium.Marker(coord).add_to(m)
    imdat = m._to_png(5)
    im = Image.open(io.BytesIO(imdat))
    return im

def _query(q: str) -> Tuple[str | List[Tuple[float, float]], Image.Image | None]:
    try:
        osm_result = overpass.query(q)
        coords = list(map(lambda x: (float(x.lat), float(x.lon)), osm_result.nodes))
        x_cords = list(map(lambda x: x[0], coords))
        y_cords = list(map(lambda x: x[1], coords))
        if len(coords) == 0:
            return prompting.DELTA_TOO_LITTLE, None
        if len(coords) > 1:
            x_std = statistics.stdev(x_cords)
            y_std = statistics.stdev(y_cords)
            if x_std > STDEV_THRESHOLD or y_std > STDEV_THRESHOLD:
                return prompting.TOO_SPREAD, render(coords)
        return coords, render(coords)
    except Exception as e:
        print(e)
        return str(e) + "\n Please Adjust the OSM query to fix this issue.", None


@tool("Overpass Turbo")
def query(q: str) -> Any:
    """
    Skims through the query string for a chunk of OSM Query, executes the query, and returns the resulting
    lat long pairs.
    Use this tool to pinpoint locations on the map. Be specific about your conditions.
    For example, a valid input would be:
    'Starbucks next to train stations in New York'
    Do not include a codeblock in function call. Jus the raw query.
    :param q: The overpass turbo query you are running. ALWAYS pass in a full overpass turbo query.
    :return: list of tuples if valid, otherwise returns a string representing the next prompt
    """
    r = requests.post("https://aapi.tech-demos.de/overpassnl/overpassnl", json={"usertext": q})
    if r.status_code != 200:
        return f"Something went wrong with overpass query: {r.content}. Please try again."
    osm_query = r.json()["osmquery"]
    print("OSM QUERY:\n", osm_query)
    res, img = _query(osm_query)
    rsp = f"OSM Query result: {res}"
    if isinstance(img, Image.Image):
        loc = utils.save_img(img, "osm_query_res")
        rsp += "\n" + utils.image_to_prompt(str(loc))
    return rsp

@tool("Show Coordinates", return_direct=True)
def show_coords(coords: str):
    """
    Shows the coordinates on a map. Use this when you are certain of the final coordinates and want to display that to user.
    Eg. [(-122.123, 45.123), (-122.123, 45.123)]
    :param coords: (lat, lon) or [(lat, lon)...]
    :return:
    """
    print("RESULT COORDS:",  coords)

if __name__ == '__main__':
    QUERY = "Find me Korean Steak House in Washington next to Monroe St"
    print("querying...")
    q_res = query(QUERY)
    print("query result:", q_res)
