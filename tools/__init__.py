from . import osm, osm_wiki, nomantim, geo_clip

TOOLS = [osm.query, osm_wiki.search, nomantim.search_raw, osm.show_coords, geo_clip.geoclip_predict]