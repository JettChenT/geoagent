from typing import List

from langchain_core.tools import BaseTool

from . import osm, osm_wiki, nomantim, geo_clip

TOOLS: List[BaseTool] = [osm.query, osm_wiki.search, nomantim.search_raw, osm.show_coords, geo_clip.geoclip_predict]

tools_map = {tool.name: tool for tool in TOOLS}
def find_tool(name: str) -> BaseTool | None:
    for tool in TOOLS:
        if tool.name in name:
            return tool
