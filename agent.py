from connector import VLLM
from overpy import Overpass
from prompting import *
from pathlib import Path
from PIL import Image
from typing import List, Tuple
from utils import find_last_code_block
from rich import print
from connector import *
from osm import OSMJudge

class Agent:
    DEPTH_THRESHOLD = 10
    def __init__(self, vllm: VLLM):
        self.vllm = vllm
        self.osm = OSMJudge()

    def chain(self, prompt, image: Path | Image.Image | None = None, depth: int = 0):
        print("--------------------")
        print("DEPTH:", depth)
        print("PROMPT:", prompt)
        print("--------------------")
        if depth > self.DEPTH_THRESHOLD:
            raise RecursionError("Chain depth threshold exceeded. Aborting.")
        res = self.vllm.prompt(prompt, image)
        print("RESPONSE:", res)
        osm_res = self.osm.query(find_last_code_block(res))
        print("------- OSM Response --------")
        print(osm_res)
        if isinstance(osm_res, str):
            return self.chain(osm_res, depth=depth + 1)
        else:
            return osm_res

if __name__ == '__main__':
    agent = Agent(GPT4Vision())
    # agent = Agent(LLAVA(Path('../models/llava/ggml-model-q4_k.gguf'), Path('../models/llava/mmproj-model-f16.gguf')))
    print(agent.chain(INITIAL_PROMPT, Path('./images/NY.png')))