import logging
import os
import sys
import pandas as pd
import numpy as np
import time
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
    if not (target_folder / 'coords.csv').exists():
        image_files = [f for f in os.listdir(target_folder) if f.endswith('.jpg')]
        image_files = [os.path.join(target_folder, f) for f in image_files]
        coordinates = [extract_coordinates(f) for f in image_files]
        filenames = [os.path.basename(f) for f in image_files]
        df = pd.DataFrame(
            {'image': filenames,
             'latitude': [c[0] for c in coordinates],
             'longitude': [c[1] for c in coordinates],
             'pred': ""}
        )
        df.to_csv(target_folder / 'coords.csv', index=False)
    cords = pd.read_csv(target_folder / 'coords.csv')
    if 'pred' not in cords.columns:
        cords['pred'] = ""
    srv, sub_thread = start_srv()
    sio_sub = SIOSubscriber(srv)
    cords = shuffle(cords)
    cords.reset_index(drop=True, inplace=True)
    input(f"this will evaluate {len(cords)} images. Press enter to start.")
    sio_sub.push("global_info_set", ("task", "Evaluating Dataset"))
    print("starting...")
    to_evaluate = cords[cords['pred'].isna()]
    for i, row in to_evaluate.iterrows():
        t_begin = time.time()
        agent = Agent(Gpt4Vision(), subscriber=sio_sub)
        img_path = target_folder / row['image']
        sio_sub.push("global_info_set", ("progress", f"{i}/{len(to_evaluate)}"))
        sio_sub.push("global_info_set", ("image", str(img_path)))
        res = agent.lats(img_path)
        try:
            pred = utils.sanitize(res.transition.tool_input)
            cords.loc[i, 'pred'] = pred
            print(f"Predicted: {pred}")
            print(f"Actual: {row['latitude']}, {row['longitude']}")
            print(f"Progress: {i}/{len(to_evaluate)}")
            print(f"Time: {time.time() - t_begin} seconds")
            cords.to_csv(target_folder / "coords.csv", index=False)
        except Exception as e:
            logging.error(f"Error in {img_path}: {e}")

def evaluate_batch(target_folder : Path, batch_num = 10):
    pass

if __name__ == '__main__':
    evaluate(Path(sys.argv[1]))
