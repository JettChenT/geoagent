import requests
from langchain.tools import tool
from langchain_core.tools import ToolException

API_URL = "https://wiki.openstreetmap.org/api.php"

@tool("OSM Wiki Search")
def search(query: str) -> str:
    """
    Searches the OSM Wiki for a query. Use this if you are not sure about
    specific features or tags that you would use for your later Overpass Turbo Query.
    :param query:
    :return:
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json"
    }
    try:
        res = requests.get(API_URL, params=params).json()
        return str(res)
    except Exception as e:
        return "Error while querying OSM Wiki: " + str(e)


if __name__ == '__main__':
    print(search("Washington"))