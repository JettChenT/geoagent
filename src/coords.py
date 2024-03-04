from pathlib import Path
from pydantic import BaseModel
from PIL import Image
from typing import List, Tuple, Any
import pandas as pd
import io
import folium
import json

from . import utils
from .session import Session

PADDING = 0.001


# TODO: support for coords to preserve auxiliary information?
class Coords:
    coords: List[Tuple[float, float]]  # lat, lon
    auxiliary: List[Any]

    def __init__(
        self, coords: List[Tuple[float, float]], auxiliary: List[Any] | None = None
    ):
        self.coords = coords
        self.auxiliary = auxiliary or [{}] * len(coords)

    def split_latlon(self) -> Tuple[List[float], List[float]]:
        return list(map(lambda x: x[0], self.coords)), list(
            map(lambda x: x[1], self.coords)
        )

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

    def to_prompt(self, session: Session, prefix="", plain=False, render=True, store=True):
        res = ""
        if plain:
            res += f"Lat Long Coordinates: {self.coords}\n"
        if render:
            im = self.render()
            loc = utils.save_img(im, f"{prefix}coords", session)
            res += f"A rendering of the coordinates: {utils.image_to_prompt(loc)}"
        if store:
            loc = utils.find_valid_loc(session, f"{prefix}coords", ".geojson")
            self.to_geojson(loc)
            res += f"The coordinates are stored at {loc}"
        return res

    def to_csv(self, path: str | Path):
        df = pd.DataFrame(self.coords, columns=["lat", "lon"])
        df["auxiliary"] = [json.dumps(x) for x in self.auxiliary]
        df.to_geojson(path, index=False)

    @staticmethod
    def from_csv(path: str | Path):
        df = pd.read_csv(path)
        return Coords(
            coords=df[["lat", "lon"]].values.tolist(),
            auxiliary=[json.loads(x) for x in df["auxiliary"]]
            if "auxiliary" in df.columns
            else None,
        )

    def to_geojson(self, path: str | Path):
        features = []
        for coord, aux in zip(self.coords, self.auxiliary):
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": coord[::-1]
                    },
                    "properties": aux
                }
            )
        with open(path, 'w') as f:
            json.dump({
                "type": "FeatureCollection",
                "features": features
            }, f)

    @staticmethod
    def from_geojson(path: str | Path):
        with open(path, 'r') as f:
            data = json.load(f)
        coords = []
        auxiliary = []
        for feature in data["features"]:
            coords.append(feature["geometry"]["coordinates"][::-1])
            auxiliary.append(feature["properties"])
        return Coords(coords, auxiliary)

    @staticmethod
    def load(path: str | Path) -> 'Coords':
        if isinstance(path, str):
            path = Path(path)
        match path.suffix:
            case ".csv":
                return Coords.from_csv(path)
            case ".geojson":
                return Coords.from_geojson(path)
            case _:
                raise ValueError("Unsupported file format")
    def __len__(self):
        return len(self.coords)

    def __repr__(self):
        return str(self.coords)

    def __iter__(self):
        yield from self.coords
