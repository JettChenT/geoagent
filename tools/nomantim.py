from geopy import Nominatim
from langchain.tools import tool
from langchain_core.tools import ToolException

geolocator = Nominatim(user_agent="osm")

@tool("Nomantim Geocoder")
def search_raw(query: str) -> str:
    """
    Searches the OSM Wiki for a query. Use this if you are not sure about
    what are the Open Streetmap names for a general location.
    Priorize using this if you need an area name such as `United States` or `Washington`.
    Prefer not to use this if you are looking up a specific string or name, for that use Overpass Turbo.
    :param query: A single area or location you want to geocode for.
    :return:
    """
    res = geolocator.geocode(query)
    if res is None:
        return f"No results found for query: {query}, please pass in a valid location to geolocate."
    return str(res.raw)

if __name__ == '__main__':
    print(search_raw("15th Ave and Encanto Blvd, Phoenix, AZ"))