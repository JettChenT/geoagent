from .. import config
from .. import utils
from ..session import Session
from .wrapper import gtool
from tavily import TavilyClient

from concurrent.futures import ThreadPoolExecutor
import os

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@gtool("tavily_search", cached=True)
def tavily_search(query: str, session: Session):
    """
    Use the tavily search engine to look for an answer.
    This provides relevant sourcesm images, and an answer.
    In general, prefer this method of searching for answers.
    """
    res = tavily_client.search(query, include_images=True, include_answer=True, search_depth="advanced")
    if not res:
        raise Exception("No results found")
    res_pmpt = ""
    res_pmpt += f"Answer: {res['answer']}\n"

    if res['images']:
        res_pmpt += "Images: \n"
        
        def process_image(im_url):
            try:
                im_loc = utils.enforce_image(im_url, session)
                return f"{utils.image_to_prompt(im_loc, session)}\n"
            except Exception as e:
                print(e)
                return None

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_image, res['images']))
        
        for i, result in enumerate(results):
            if result:
                res_pmpt += f"Image {i}: {result}"
                
    res_pmpt += "Results: \n"
    for res in res['results']:
        res_pmpt += f"Title: {res['title']}\nContent: {res['content']}\nURL: {res['url']}\n\n"

    return res_pmpt
            
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python tavily.py <search_query>")
        sys.exit(1)
    query = sys.argv[1]
    session = Session().setup()
    try:
        result = tavily_search(query, session)
        print("Search Results:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
