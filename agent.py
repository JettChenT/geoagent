from connector import VLLM
from overpy import Overpass
from prompting import *
from pathlib import Path
from PIL import Image
from typing import List, Tuple
from utils import find_last_code_block
from rich import print
from connector import *

class Agent:
    LOWER_THRESHOLD = 1
    UPPER_THRESHOLD = 40
    DEPTH_THRESHOLD = 8

    def __init__(self, vllm: VLLM):
        self.vllm = vllm
        self.osm = Overpass()

    def proc_osm(self, query: str) -> List[Tuple[float, float]] | str:
        """
        Skims through the query string for a chunk of OSM Query, executes the query, and returns the resulting
        lat long pairs.
        :param query:
        :return:
        """
        # Look for the last markdown code block in query
        osm_query = find_last_code_block(query)
        print("QUERYING:", osm_query)
        osm_result = self.osm.query(osm_query)
        return list(map(lambda x: (float(x.lat), float(x.lon)), osm_result.nodes))

    def chain(self, prompt, image: Path | Image.Image | None = None, depth: int = 0):
        print("--------------------")
        print("DEPTH:", depth)
        print("PROMPT:", prompt)
        print("--------------------")
        if depth > self.DEPTH_THRESHOLD:
            raise RecursionError("Chain depth threshold exceeded. Aborting.")
        res = self.vllm.prompt(prompt, image)
        print("RESPONSE:", res)
        osm_res = self.proc_osm(res)
        print("------- OSM Response --------")
        print(osm_res)
        if isinstance(osm_res, str):
            return self.chain(osm_res, depth=depth + 1)
        else:
            if len(osm_res)< self.LOWER_THRESHOLD:
                return self.chain(DELTA_TOO_LITTLE, depth=depth+1)
            elif len(osm_res) > self.UPPER_THRESHOLD:
                return self.chain(DELTA_TOO_MUCH, depth=depth+1)
            else:
                return osm_res

if __name__ == '__main__':
    # agent = Agent(GPT4Vision())
    agent = Agent(LLAVA(Path('../models/llava/ggml-model-q4_k.gguf'), Path('../models/llava/mmproj-model-f16.gguf')))
    print(agent.chain(INITIAL_PROMPT, Path('./images/NY.png')))