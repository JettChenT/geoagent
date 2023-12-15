import requests

API_URL = "https://wiki.openstreetmap.org/api.php"

def search(query: str):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json"
    }
    return requests.get(API_URL, params=params).json()

if __name__ == '__main__':
    print(search("Washington"))