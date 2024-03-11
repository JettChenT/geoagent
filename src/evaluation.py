import logging
import os
import sys
import pandas as pd
import time
from pathlib import Path
from sklearn.utils import shuffle
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from multiprocessing import Value

# Assuming these modules exist and are correctly implemented
from src import utils
from .connector.gptv import Gpt4Vision
from .subscriber import SIOSubscriber
from .sock import start_srv
from .agent import Agent

csv_lock = Lock()
counter = Value('i', 0)

def find_coordinate(content, marker):
    start_index = content.find(marker)
    end_ind = content.find(b'\x00', start_index)
    return float(content[start_index + len(marker):end_ind].decode('utf-8'))


def extract_coordinates(file_path):
    longitude_marker = b'longitude:'
    latitude_marker = b'latitude:'
    contents = open(file_path, 'rb').read()
    coords = (find_coordinate(contents, latitude_marker), find_coordinate(contents, longitude_marker))
    del contents
    return coords


# Original sequential evaluation function
def evaluate(target_folder: Path):
    if not (target_folder / 'coords.csv').exists():
        image_files = [f for f in os.listdir(target_folder) if f.endswith('.jpg')]
        image_files = [os.path.join(target_folder, f) for f in image_files]
        coordinates = [extract_coordinates(f) for f in image_files]
        filenames = [os.path.basename(f) for f in image_files]
        df = pd.DataFrame(
            {'image': filenames, 'latitude': [c[0] for c in coordinates], 'longitude': [c[1] for c in coordinates],
             'pred': ""})
        df.to_csv(target_folder / 'coords.csv', index=False)

    cords = pd.read_csv(target_folder / 'coords.csv')
    if 'pred' not in cords.columns:
        cords['pred'] = ""
    srv, sub_thread = start_srv()
    sio_sub = SIOSubscriber(srv)
    cords = shuffle(cords)
    cords.reset_index(drop=True, inplace=True)
    input("This will evaluate images sequentially. Press enter to start.")
    sio_sub.push("global_info_set", ("task", "Evaluating Dataset Sequentially"))
    print("Starting...")

    for i, row in cords.iterrows():
        t_begin = time.time()
        agent = Agent(Gpt4Vision(), subscriber=sio_sub)  # Create a new Agent instance for each image
        img_path = target_folder / row['image']
        sio_sub.push("global_info_set", ("image", str(img_path)))
        try:
            res = agent.lats(img_path)
            pred = utils.sanitize(res.transition.tool_input)
            cords.loc[i, 'pred'] = pred
            print(f"Predicted: {pred} for image {row['image']}")
            print(f"Actual: {row['latitude']}, {row['longitude']}")
            print(f"Time: {time.time() - t_begin} seconds")
            cords.to_csv(target_folder / "coords.csv", index=False)  # Save after each prediction
        except Exception as e:
            logging.error(f"Error in {img_path}: {e}")


def evaluate_image(row, target_folder, sio_sub):
    agent = Agent(Gpt4Vision(), subscriber=sio_sub)
    t_begin = time.time()
    img_path = target_folder / row['image']
    sio_sub.push("global_info_set", ("image", str(img_path)))
    pred = ""
    try:
        res = agent.lats(str(img_path))
        sio_sub.push("set_session_info_key", (agent.session.id, "completed", True))
        pred = utils.sanitize(res.transition.tool_input)
        print(f"Predicted: {pred} for image {row['image']}")
        print(f"Actual: {row['latitude']}, {row['longitude']}")
        print(f"Time: {time.time() - t_begin} seconds")
        with csv_lock:
            csv_path = target_folder / 'coords.csv'
            cords_df = pd.read_csv(csv_path)
            cords_df.loc[cords_df['image'] == row['image'], 'pred'] = pred
            cords_df.to_csv(csv_path, index=False)
        global counter
        with counter.get_lock():
            counter.value += 1
            sio_sub.push("global_info_set", ("progress", counter.value))
    except Exception as e:
        logging.error(f"Error in {img_path}: {e}")
        sio_sub.push("set_session_info_key", (agent.session.id, "error", str(e)))


def evaluate_batched(target_folder: Path, batch_size=10):
    csv_path = target_folder / 'coords.csv'
    cords = pd.read_csv(csv_path)
    if 'pred' not in cords.columns:
        cords['pred'] = ""
    srv, sub_thread = start_srv()
    sio_sub = SIOSubscriber(srv)
    cords = shuffle(cords)
    cords.reset_index(drop=True, inplace=True)
    input("This will evaluate images in batches. Press enter to start.")
    sio_sub.push("global_info_set", ("task", "Evaluating Dataset Batched"))
    sio_sub.push("global_info_set", ("total", len(cords)))
    print("Starting...")

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        future_to_row = {executor.submit(evaluate_image, row, target_folder, sio_sub): row for _, row
                         in cords.iterrows()}
        for future in as_completed(future_to_row):
            try:
                future.result()
            except Exception as exc:
                print(f'Generated exception: {exc}')


if __name__ == '__main__':
    path = Path(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == 'batched':
        evaluate_batched(path)
    else:
        evaluate(path)
