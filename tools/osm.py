from overpy import Overpass
from typing import List, Tuple
import folium
import prompting
import io
from PIL import Image
import statistics

PADDING = 0.001
overpass = Overpass()
STDEV_THRESHOLD = 0.001


def query(q: str) -> List[Tuple[float, float]] | Tuple[str, Image.Image|None]:
    """
    Skims through the query string for a chunk of OSM Query, executes the query, and returns the resulting
    lat long pairs.
    :param q:
    :return: list of tuples if valid, otherwise returns a string representing the next prompt
    """
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
        return coords
    except Exception as e:
        print(e)
        return str(e) + "\n Please Adjust the OSM query to fix this issue.", None


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

if __name__ == '__main__':
    QUERY = """
area["name"~".*Washington.*"];
way["name"~"Monroe.*St.*NW"](area) -> .mainway;

(
  nwr(around.mainway:500)["name"~"Korean.*Steak.*House"];

  // Find nearby businesses with CA branding
  nwr(around.mainway:500)["name"~"^CA.*"];
  
  // Look for a sign with the words "Do not block"
  node(around.mainway:500)["traffic_sign"~"Do not block"];
);

out center;
    """
    print("querying...")
    coords = query(QUERY)
    print(f"found {len(coords)} results, rendering...")
    render(coords).show()