from pathlib import Path
from pydantic import BaseModel
from PIL import Image
from typing import List, Tuple
import pandas as pd
import io
import folium

import utils

PADDING = 0.001

# TODO: support for coords to preserve auxiliary information?
class Coords:
    coords: List[Tuple[float, float]] # lat, lon

    def __init__(self, coords: List[Tuple[float, float]]):
        self.coords = coords

    def split_latlon(self) -> Tuple[List[float], List[float]]:
        return list(map(lambda x: x[0], self.coords)), list(map(lambda x: x[1], self.coords))

    def render(self) -> Image.Image:
        """
        Visualizes the coordinates on a map
        :param coords:
        :return:
        """
        x_cords, y_cords = self.split_latlon()
        bbox = [[min(x_cords), min(y_cords)], [max(x_cords), max(y_cords)]]
        m = folium.Map()
        m.fit_bounds(bbox, padding=[PADDING] * 4)
        for coord in self.coords:
            folium.Marker(coord).add_to(m)
        imdat = m._to_png(5)
        im = Image.open(io.BytesIO(imdat))
        return im

    def to_csv(self, path: str | Path):
        df = pd.DataFrame(self.coords, columns=["lat", "lon"])
        df.to_csv(path, index=False)

    def to_prompt(self, prefix="", plain=False, render=True, store=True):
        res = ""
        if plain:
            res += f"Lat Long Coordinates: {self.coords}\n"
        if render:
            im = self.render()
            loc = utils.save_img(im, f"{prefix}coords")
            res += f"A rendering of the coordinates: {utils.image_to_prompt(loc)}"
        if store:
            loc = utils.find_valid_loc(f"{prefix}coords", ".csv")
            self.to_csv(loc)
            res += f"The coordinates are stored at {loc}"
        return res

    @staticmethod
    def from_csv(path: str | Path):
        df = pd.read_csv(path)
        return Coords(coords=df.values.tolist())

    def __len__(self):
        return len(self.coords)

    def __repr__(self):
        return str(self.coords)

    def __iter__(self):
        yield from self.coords
