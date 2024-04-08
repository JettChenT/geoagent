import os
import torch
from dataclasses import dataclass

from torch.utils.data import DataLoader
from .sample4geo.dataset.cvusa import CVUSADatasetEval
from .sample4geo.transforms import get_transforms_val
from .sample4geo.evaluate.cvusa_and_cvact import evaluate, calc_sim
from .sample4geo.model import TimmModel
from .inference import Configuration
import cv2
import numpy as np
from torch.utils.data import Dataset
import pandas as pd
import random
import copy
import torch
from tqdm import tqdm
import time

config = Configuration()


class DataSetEval(Dataset):
    def __init__(
        self,
        data_folder,
        img_type,
        transforms=None,
    ):
        super().__init__()
        self.data_folder = data_folder
        self.img_type = img_type  # 'ground' or 'aerial'
        label = range(19) if img_type == "aerial" else [0]
        self.label = np.array(label)
        self.transforms = transforms

    def __getitem__(self, index):
        file_name = f"{index}.png"
        if self.img_type == "aerial":
            file_name = "satellite_res" + file_name
        img = cv2.imread(f"{self.data_folder}/{self.img_type}/{file_name}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        label = torch.tensor(self.label[index], dtype=torch.long)
        if self.transforms is not None:
            img = self.transforms(image=img)["image"]

        return img, label

    def __len__(self):
        return 19 if self.img_type == "aerial" else 1


if __name__ == "__main__":
    model = TimmModel(config.model, pretrained=True, img_size=config.img_size)
    data_config = model.get_config()
    print(data_config)
    mean = data_config["mean"]
    std = data_config["std"]
    img_size = config.img_size

    image_size_sat = (img_size, img_size)

    new_width = config.img_size * 2
    new_hight = round((224 / 1232) * new_width)
    img_size_ground = (new_hight, new_width)

    # load pretrained Checkpoint
    if config.checkpoint_start is not None:
        print("Start from:", config.checkpoint_start)
        model_state_dict = torch.load(
            config.checkpoint_start, map_location=torch.device("cpu")
        )
        model.load_state_dict(model_state_dict, strict=False)

    # Data parallel
    print("GPUs available:", torch.cuda.device_count())
    if torch.cuda.device_count() > 1 and len(config.gpu_ids) > 1:
        model = torch.nn.DataParallel(model, device_ids=config.gpu_ids)

    # Model to device
    model = model.to(config.device)

    print("\nImage Size Sat:", image_size_sat)
    print("Image Size Ground:", img_size_ground)
    print("Mean: {}".format(mean))
    print("Std:  {}\n".format(std))

    sat_transforms_val, ground_transforms_val = get_transforms_val(
        image_size_sat,
        img_size_ground,
        mean=mean,
        std=std,
    )

    aerial_dataset = DataSetEval(
        config.data_folder, "aerial", transforms=sat_transforms_val
    )
    aerial_dataloader = DataLoader(
        aerial_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=True,
    )
    ground_dataset = DataSetEval(
        config.data_folder, "ground", transforms=ground_transforms_val
    )
    ground_dataloader = DataLoader(
        ground_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=True,
    )

    print(len(aerial_dataset), len(ground_dataset))
    res = evaluate(
        config=config,
        model=model,
        reference_dataloader=aerial_dataloader,
        query_dataloader=ground_dataloader,
        cleanup=True,
    )
    print(res)
