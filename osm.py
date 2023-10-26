from overpy import Overpass
import prompting
from typing import List, Tuple

class OSMJudge:
    LOWER_THRESHOLD = 1
    UPPER_THRESHOLD = 40

    def __init__(self):
        self.overpass = Overpass()

    def query(self, query: str) -> List[Tuple[float, float]] | str:
        """
        Skims through the query string for a chunk of OSM Query, executes the query, and returns the resulting
        lat long pairs.
        :param query:
        :return: list of tuples if valid, otherwise returns a string representing the next prompt
        """
        try:
            osm_result = self.overpass.query(query)
            coords = list(map(lambda x: (float(x.lat), float(x.lon)), osm_result.nodes))
            print(coords)
            if len(coords) < self.LOWER_THRESHOLD:
                return prompting.DELTA_TOO_LITTLE
            elif len(coords) > self.UPPER_THRESHOLD:
                return prompting.DELTA_TOO_MUCH
            return coords
        except Exception as e:
            print(e)
            return str(e)