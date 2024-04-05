from typing import List

from langchain_core.tools import BaseTool

from . import osm, nominatim, geo_clip, vpr, azure, serp, pplx, Sample4Geo, misc
from .gcp import streetview, places
from .wrapper import GToolWrap, proc_tools, gtool
from .response import ToolResponse

# noinspection PyTypeChecker
TOOLS: List[GToolWrap] = [
    # osm.query,
    # osm.wiki_search,
    osm.show_coords,
    # nominatim.search_raw,
    geo_clip.geoclip_predict,
    streetview.get_panos,
    vpr.locate_image,
    places.text_search,
    places.plot_satellite,
    # azure.bing.search_text,
    # azure.bing.search_image,
    serp.search_lens,
    serp.image_search,
    pplx.ask,
    Sample4Geo.satellite_locate,
    misc.decide,
    misc.add_clue,
    misc.save_coords,
    misc.plan_ahead
]
