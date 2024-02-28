# Utility functions for machine learning
import os
from pathlib import Path
from typing import List

import torch
from PIL import Image


def using_mps():
    return (
        torch.backends.mps.is_available()
        and torch.backends.mps.is_built()
        and os.environ.get("USE_MPS", "0") == "1"
    )


def load_image(loc: str | Path):
    return Image.open(loc).convert("RGB")

def cosine_similarity(vec1: torch.Tensor, vec2: torch.Tensor) -> torch.Tensor:
    dot_product = vec1 @ vec2.T
    norm_vec1 = torch.norm(vec1)
    norm_vec2 = torch.norm(vec2, dim=1)
    similarity = dot_product / (norm_vec1 * norm_vec2)
    return similarity

