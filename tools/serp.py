import io
import os
from pathlib import Path
import requests
import dotenv
from serpapi import GoogleSearch
from PIL import Image
import utils
from langchain.tools import tool

from utils import encode_image


SERP_API_KEY = os.environ['SERP_API_KEY']
TOP_N = 15

@tool("Google Lens Search")
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
    res = ""
    for (i,v) in enumerate(visual_matches[:TOP_N]):
        im_url = v['thumbnail']
        # download the image
        img_data = requests.get(im_url).content
        im = Image.open(io.BytesIO(img_data))
        saved_loc = utils.save_img(im, "serp")
        res += f"Result {i}: \n Title:{v['title']} \n {utils.image_to_prompt(saved_loc)}\n"
    return res

if __name__ == '__main__':
    dotenv.load_dotenv()
    print(search_img._run('./images/anon/10.png'))