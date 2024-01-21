import requests
from langchain.tools import tool


@tool("Taginfo Query")
def taginfo_query(q: str):
    """
    Queries the Taginfo API for a query.
    This can be used to construct overpass queries.
    Use this when you don't know the correct tag for a query.
    :param q: The query to search for.
    :return:
    """
    r = requests.get(
        "https://taginfo.openstreetmap.org/api/4/keys/all",
        params={
            "query": q,
            "sortname": "count_all",
            "sortorder": "desc",
            "rp": 20,
            "page": 1,
        },
    ).json()
    return "Results of Taginfo Query: " + str(r)


if __name__ == "__main__":
    print(taginfo_query._run("restaurant"))
