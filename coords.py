from pathlib import Path
from pydantic import BaseModel
from typing import List, Tuple
import pandas as pd

class Coords(BaseModel):
    coords: List[Tuple[float, float]] # lat, lon

    def __init__(self, coords: List[Tuple[float, float]]):
        self.coords = coords

    def split_latlon(self) -> Tuple[List[float], List[float]]:
        return list(map(lambda x: x[0], self.coords)), list(map(lambda x: x[1], self.coords))

    def to_csv(self, path: str | Path):
        df = pd.DataFrame(self.coords, columns=["lat", "lon"])
        df.to_csv(path, index=False)

    @staticmethod
    def from_csv(path: str | Path):
        df = pd.read_csv(path)
        return Coords(coords=df.values.tolist())

    def __len__(self):
        return len(self.coords)

    def __repr__(self):
        return str(self.coords)