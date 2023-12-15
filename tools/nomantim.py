from geopy import Nominatim
geolocator = Nominatim(user_agent="osm")

def search_raw(query: str):
    return geolocator.geocode(query).raw