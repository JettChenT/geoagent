from typing import List

from langchain_core.tools import BaseTool

from . import osm, nominatim, geo_clip, vpr, azure, serp, pplx
from .gcp import streetview, places

# noinspection PyTypeChecker
TOOLS: List[BaseTool] = [
    osm.query,
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
    serp.search_img,
    pplx.ask,
]

tools_map = {tool.name: tool for tool in TOOLS}


def find_tool(name: str) -> BaseTool | None:
    for tool in TOOLS:
        if tool.name in name:
            return tool
