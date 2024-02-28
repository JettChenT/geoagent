import logging
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.utils import shuffle

from src import utils
from .connector.gptv import Gpt4Vision
from .subscriber import SIOSubscriber
from .sock import start_srv
from .agent import Agent


def find_coordinate(content, marker):
    start_index = content.find(marker)
    end_ind = content.find(b'\x00', start_index)
    return float(content[start_index + len(marker):end_ind].decode('utf-8'))

def extract_coordinates(file_path):
    # Markers to search for
    longitude_marker = b'longitude:'
    latitude_marker = b'latitude:'
    contents = open(file_path, 'rb').read()
    coords = (find_coordinate(contents, latitude_marker), find_coordinate(contents, longitude_marker))
    del contents
    return coords

def evaluate(target_folder: Path):
    cords = pd.read_csv(target_folder / 'coords.csv')
    srv, sub_thread = start_srv()
    sio_sub = SIOSubscriber(srv)
    cords = shuffle(cords)
    cords.reset_index(drop=True, inplace=True)
    input(f"this will evaluate {len(cords)} images. Press enter to start.")
    for i, row in cords.iterrows():
        agent = Agent(Gpt4Vision(), subscriber=sio_sub)
        img_path = target_folder / row['image']
        res = agent.lats(img_path)
        try:
            pred = utils.sanitize(res.transition.tool_input)
            cords.loc[i, 'pred'] = pred
            print(f"Predicted: {pred}")
            print(f"Actual: {row['latitude']}, {row['longitude']}")
            print(f"Progress: {i}/{len(cords)}")
            cords.to_csv(target_folder/"eval.csv")
        except Exception as e:
            logging.error(f"Error in {img_path}: {e}")


if __name__ == '__main__':
    evaluate(Path(sys.argv[1]))
