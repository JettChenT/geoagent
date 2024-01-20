from pathlib import Path

import utils
import requests
from rich import print
from langchain.tools import tool
from .auth import ENDPOINT, HEADERS

@tool("Bing Search")
def search_text(query, mkt='en-US'):
    """
    Searches Bing for a query.
    :param query: The query to search for.
    :param mkt: The market to search in.
    :return:
    """
    params = {'q': query, 'mkt': mkt}
    response = requests.get(ENDPOINT+"/search", headers=HEADERS, params=params)
    return response.json()

@tool("Bing Image Search")
def search_image(img_path: str | Path, mkt='en-US'):
    """
    Searches Bing for an image.
    :param img_path: The path to the image to search for.
    :param mkt: The market to search in.
    :return:
    """
    # TODO: Improve the output of this to the LLM
    if isinstance(img_path, str):
        img_path = Path(img_path)
    params = {'mkt': mkt}
    file = {'image': ('query_image', utils.read_image(img_path))}
    response = requests.post(ENDPOINT+"/images/visualsearch", headers=HEADERS, params=params, files=file)
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    print(search_image._run('./images/anon/10.png'))