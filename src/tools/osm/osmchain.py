from langchain.tools import tool
import requests
from rich import print

@tool("taginfo_key")
def key_search(q:str):
    """
    Searches the taginfo database for attributes available
    :param q:
    :return:
    """
    r = requests.get(f"https://taginfo.openstreetmap.org/api/4/keys/all", params={
        "query": q,
        "page": "1",
        "rp": "10",
        "sortname": "count_all",
        "sortorder": "desc",
        "include": "prevalent_values"
    })
    return r.json()

@tool("taginfo_value")
def value_search(q:str):
    """
    Searches the taginfo database for attributes available
    :param q:
    :return:
    """
    r = requests.get(f"https://taginfo.openstreetmap.org/api/4/search/by_value", params={
        "query": q,
        "page": "1",
        "rp": "10",
        "sortname": "count_all",
        "sortorder": "desc",
        "include": "prevalent_values"
    })
    return r.json()

@tool("taginfo_keyvalue")
def key_value_search(k:str, v:str):
    """
    Searches the taginfo database for attributes available
    :param k:
    :param v:
    :return:
    """
    r1 = key_search(k)
    r2 = value_search(v)
    return {
        "keys": r1,
        "values": r2
    }

if __name__ == '__main__':
    print(key_search("highway"))
    print("-"*10)
    print(value_search("highway"))
