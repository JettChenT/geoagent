import io
import os
from pathlib import Path
import requests
import dotenv
from serpapi import GoogleSearch
from functools import cache
from PIL import Image
from .. import utils
from .wrapper import Session, gtool
from concurrent.futures import ThreadPoolExecutor, as_completed

SERP_API_KEY = os.environ["SERP_API_KEY"]
TOP_N = 15

def process_single_result(v, i, session):
    try:
        # TODO
        im_url = v["thumbnail"]
        img_data = requests.get(im_url).content
        im = Image.open(io.BytesIO(img_data))
    except Exception as e:
        im_url = v["thumbnail"]
        img_data = requests.get(im_url).content
        im = Image.open(io.BytesIO(img_data))
    saved_loc = utils.save_img(im, "serp", session)
    return f"Result {i}: \n Title:{v['title']} \n {utils.image_to_prompt(saved_loc, session)}\n"

def proc_image_results(results: dict, session: Session, top_n=TOP_N) -> str:
    with ThreadPoolExecutor() as executor:
        res = list(executor.map(process_single_result, results[:top_n], range(top_n), [session]*top_n))
    return "".join(res)

@gtool("google_lens", cached=True)
def search_lens(img_id: str, session: Session):
    """
    Searches Google Lens for an image (img -> content, relevant images)
    :param img_id: The image id
    :return:
    """
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_lens",
        "url": utils.upload_image(session, Path(session.get_loc(img_id))),
    }
    print(params)
    search = GoogleSearch(params)
    results = search.get_dict()
    if "visual_matches" not in results:
        return f"Error: {results['error']}" if "error" in results else "No results found."
    visual_matches = results["visual_matches"]
    return proc_image_results(visual_matches, session)

@gtool("google_image_search", cached=True)
def image_search(query: str, session: Session):
    """
    Searches Google Images for a query (text query -> images, descriptions)
    :param query: The query to search for
    :return:
    """
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_images",
        "q": query,
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    if "images_results" not in results:
        return f"Error: {results['error']}" if "error" in results else "No results found."
    images_results = results["images_results"]
    return proc_image_results(images_results, session)



if __name__ == "__main__":
    from rich import print
    dotenv.load_dotenv()
    session = Session()
    image_search = image_search.to_tool(session)
    print(image_search("The White House"))
