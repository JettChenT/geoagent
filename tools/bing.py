from pathlib import Path

import utils
import json
import dotenv
import requests
import os
from rich import print
from langchain.tools import tool

dotenv.load_dotenv()

SUBSCRIPTION_KEY = os.environ['BING_SEARCH_V7_SUBSCRIPTION_KEY']
ENDPOINT = os.environ['BING_SEARCH_V7_ENDPOINT']
HEADERS = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY}

@tool
def search_text(query, mkt='en-US'):
    params = {'q': query, 'mkt': mkt}
    response = requests.get(ENDPOINT+"/search", headers=HEADERS, params=params)
    return response.json()

@tool
def search_image(img_path: str | Path, mkt='en-US'):
    if isinstance(img_path, str):
        img_path = Path(img_path)
    params = {'mkt': mkt}
    file = {'image': ('query_image', utils.read_image(img_path))}
    response = requests.post(ENDPOINT+"/images/visualsearch", headers=HEADERS, params=params, files=file)
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    print(search_image('./images/hartford.png'))