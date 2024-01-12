from .auth import GOOGLE_MAPS_API_KEY
from coords import Coords

import requests

AUTH_HEAD = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': GOOGLE_MAPS_API_KEY
}

def wrap_auth(head):
    return dict(head, **AUTH_HEAD)

def text_search(query: str):
    """
    Returns information about a location based on a text query. Uses Google Places API.
    :param query: the text query
    :return:
    """
    r = requests.post("https://places.googleapis.com/v1/places:searchText",
                      json={"textQuery": query},
                      headers=wrap_auth({"X-Goog-FieldMask": "places.id,places.displayName,places.location"})
                      )
    res_data = r.json()
    res_coords = Coords([(x['location']['latitude'], x['location']['longitude']) for x in res_data['places']])
    return f"Results for query: {res_data}\n Coordinates: {res_coords.to_prompt('textsearch_')}"


if __name__ == '__main__':
    print(text_search("shopping center in Kryvyi Rih"))