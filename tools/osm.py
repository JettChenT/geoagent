from overpy import Overpass
from typing import List, Tuple
import folium
import prompting
import io
from PIL import Image

LOWER_THRESHOLD = 1
UPPER_THRESHOLD = 40
PADDING = 0.001
overpass = Overpass()


def query(query: str) -> List[Tuple[float, float]] | str:
    """
    Skims through the query string for a chunk of OSM Query, executes the query, and returns the resulting
    lat long pairs.
    :param query:
    :return: list of tuples if valid, otherwise returns a string representing the next prompt
    """
    try:
        osm_result = overpass.query(query)
        coords = list(map(lambda x: (float(x.lat), float(x.lon)), osm_result.nodes))
        print(coords)
        if len(coords) < LOWER_THRESHOLD:
            return prompting.DELTA_TOO_LITTLE
        elif len(coords) > UPPER_THRESHOLD:
            return prompting.DELTA_TOO_MUCH
        return coords
    except Exception as e:
        print(e)
        return str(e) + "\n Please Adjust the OSM query to fix this issue."


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