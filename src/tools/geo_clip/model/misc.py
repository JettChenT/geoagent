import pandas as pd
import numpy
import torch


def load_gps_data(path):
    df = pd.read_csv(path)

    # Extract the 'LAT' and 'LON' columns and convert them into a tensor
    tensor = torch.tensor(df[["LAT", "LON"]].values)

    return tensor
