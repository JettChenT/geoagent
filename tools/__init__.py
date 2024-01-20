from typing import List

from langchain_core.tools import BaseTool

from . import osm, nominatim, geo_clip, vpr, bing
from .gcp import streetview, places

# noinspection PyTypeChecker
TOOLS: List[BaseTool] = [osm.query,
                         osm.wiki_search,
                         osm.show_coords,
                         nominatim.search_raw,
                         geo_clip.geoclip_predict,
                         streetview.get_panos,
                         vpr.locate_image,
                         places.text_search,
                         places.plot_satellite,
                         bing.search_text,
                         bing.search_image
                         ]

tools_map = {tool.name: tool for tool in TOOLS}
def find_tool(name: str) -> BaseTool | None:
    for tool in TOOLS:
        if tool.name in name:
            return tool
