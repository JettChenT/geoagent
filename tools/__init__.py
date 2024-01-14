from typing import List

from langchain_core.tools import BaseTool

from . import osm, osm_wiki, nominatim, geo_clip, vpr
from .gcp import streetview, places

# noinspection PyTypeChecker
TOOLS: List[BaseTool] = [osm.query,
                         osm_wiki.search,
                         nominatim.search_raw,
                         osm.show_coords,
                         geo_clip.geoclip_predict,
                         streetview.get_panos,
                         vpr.locate_image,
                         places.text_search,
                         places.plot_satellite
                         ]

tools_map = {tool.name: tool for tool in TOOLS}
def find_tool(name: str) -> BaseTool | None:
    for tool in TOOLS:
        if tool.name in name:
            return tool
