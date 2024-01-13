import torch
import numpy as np
from PIL import Image
from typing import List
import torchvision.transforms as transforms
from pathlib import Path

model = None
base_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])


def load_image(loc: str|Path):
    return Image.open(loc).convert("RGB")

def get_model():
    global model
    if model is not None:
        return model
    model = torch.hub.load("gmberton/eigenplaces", "get_trained_model", backbone="ResNet50", fc_output_dim=2048)
    return model

def weight_im(im: Image.Image | List[Image.Image]):
    mod = get_model()
    if not isinstance(im, list):
        im = [im]
    input_tensor = torch.stack([base_transform(i) for i in im])
    output = mod(input_tensor)
    return output

def cosine_similarity(vec1: torch.Tensor, vec2: torch.Tensor) -> torch.Tensor:
    dot_product = vec1 @ vec2.T
    norm_vec1 = torch.norm(vec1)
    norm_vec2 = torch.norm(vec2, dim=1)
    similarity = dot_product / (norm_vec1 * norm_vec2)
    return similarity

def loc_sim(target: Image.Image, db: List[Image.Image]):
    w_target = weight_im(target)
    w_db = weight_im(db)
    print(w_target.shape, w_db.shape)
    s = cosine_similarity(w_target, w_db)
    return s

if __name__ == '__main__':
    res = loc_sim(
        load_image('./ds/query.png'),
        [load_image(f'../../run/streetview_res{i}.png') for i in range(49)]
    )
    print(res)
    print(torch.argsort(res))
