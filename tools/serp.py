import os
from pathlib import Path
import requests
import dotenv
from serpapi import GoogleSearch
import urllib.parse
import utils

from utils import encode_image

dotenv.load_dotenv()

SERP_API_KEY = os.environ['SERP_API_KEY']
TOP_N = 15

def search_img(img_path:str):
    """
    Searches Google Lens for an image
    :param img_path:
    :return:
    """
    params = {
        'api_key': SERP_API_KEY,
        'engine': "google_lens",
        'url': utils.upload_image(Path(img_path))
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    # print(results)
    visual_matches = results['visual_matches']
    return visual_matches

if __name__ == '__main__':
    from rich import print
    print(search_img('./images/anon/10.png'))