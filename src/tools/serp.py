import io
import os
from pathlib import Path
import requests
import dotenv
from serpapi import GoogleSearch
from functools import cache
from PIL import Image
from .. import utils
from .wrapper import Session, gtool, ToolResponse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

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

def proc_image_results(results: dict, session: Session, top_n=TOP_N) -> ToolResponse:
    with ThreadPoolExecutor() as executor:
        res = list(executor.map(process_single_result, results[:top_n], range(top_n), [session]*top_n))
    return ToolResponse("".join(res), {
        "images": [v['thumbnail'] for v in results[:top_n]]
    })

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

@gtool("google_search", cached=True)
def google_search(query: str):
    """
    Searches Google for a query (text query -> snippets, links)
    :param query: The query to search for
    :return:
    """
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google",
        "q": query,
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    if "organic_results" not in results:
        return f"Error: {results['error']}" if "error" in results else "No results found."
    organic_results = results["organic_results"]
    res = []
    
    if "answer_box" in results and results['answer_box']['type'] == 'organic_result':
        res.append(f"Answer box found: {json.dumps(results['answer_box'], indent=2)}\n")

    for i, v in enumerate(organic_results[:TOP_N]):
        highlighted = ';'.join(v['snippet_highlighted_words']) if 'snippet_highlighted_words' in v else 'None'
        res.append(f"Result {i}: \n Title:{v['title']} \n {v['snippet']}\n Highlighted: {highlighted}\n")
    return ToolResponse("\n".join(res), {
        "links": [v['link'] for v in organic_results[:TOP_N]],
        "full_results": results,
        "text": '\n'.join(res), 
    })

if __name__ == "__main__":
    from rich import print
    dotenv.load_dotenv()
    print(google_search("Location of building fire in Shebekino"))
