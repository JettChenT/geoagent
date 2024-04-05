from geopy import Nominatim
from langchain.tools import tool
from langchain_core.tools import ToolException

from .. import utils
from ..coords import Coords
from .wrapper import gtool, Session

geolocator = Nominatim(user_agent="OSM Querying Geocoder", timeout=10)


@gtool("Nominatim Geocoder")
def search_raw(query: str, session: Session) -> str:
    """
    Searches the OSM Wiki for a query. Use this if you are not sure about
    what are the Open Streetmap names for a general location.
    Priorize using this if you need an area name such as `United States` or `Washington`.
    When looking for intersections, use the symbol & instead of `and`.
    There might be multiple results for a query. If that is the case, use from it the one that is most relevant to you.
    Do not use this if you are looking up a specific string or name, for that use Overpass Turbo.
    :param query: A single area or location you want to geocode for.
    :return:
    """
    try:
        res = geolocator.geocode(query, exactly_one=False)
        if res is None:
            return f"No results found for query: {query}, please pass in a valid location to geolocate."
        raw_res = str([r.raw for r in res])
        coords = Coords([(d.latitude, d.longitude) for d in res])
        coords_render = coords.render()
        loc = utils.save_img(coords_render, "nominatim_query_res", session)
        dump_loc = utils.find_valid_loc(session, "nominatim_query_res", ".geojson")
        coords.save_geojson(dump_loc)
        return f"""Nominatim Query Results: {raw_res} \n The coordinates are stored at {dump_loc} \n A rendering of the coordinates: {utils.image_to_prompt(loc, session)}"""
    except Exception as e:
        return (
            "Error while querying Nominatim Geocoder"
            + str(e)
            + "\n Please pass in a valid query, or try a different tool."
        )


if __name__ == "__main__":
    print(search_raw("7th Ave, New York City"))
