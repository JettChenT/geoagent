from prompting import *
from utils import find_last_code_block
from rich import print
from connector import *
from osm import OSMJudge

class Agent:
    DEPTH_THRESHOLD = 10
    def __init__(self, vllm: VLLM):
        self.vllm = vllm
        self.osm = OSMJudge()
        self.depth = 0

    def chain(self, prompt, image: Path | Image.Image | None = None):
        self.depth+=1
        print("--------------------")
        print("DEPTH:", self.depth)
        print("PROMPT:", prompt)
        print("--------------------")
        if self.depth > self.DEPTH_THRESHOLD:
            raise RecursionError("Chain depth threshold exceeded. Aborting.")
        res = self.vllm.prompt(prompt, image)
        print("RESPONSE:", res)
        osm_res = self.osm.query(find_last_code_block(res))
        print("------- OSM Response --------")
        print(osm_res)
        if isinstance(osm_res, str):
            return self.chain(osm_res)
        else:
            return self.human(osm_res)

    def human(self, osm_res):
        print("---------- Geolocation Agent has found relevant coordinates! -----------")
        print(osm_res)
        r = input("Do you find this result relevant? [Y/n]")
        if r.lower() == "n":
            prompt = input("Please enter what needs to be adjusted in our current search")
            return self.chain(prompt)
        return osm_res


if __name__ == '__main__':
    agent = Agent(GPT4Vision())
    # agent = Agent(LLAVA(Path('../models/llava/ggml-model-q4_k.gguf'), Path('../models/llava/mmproj-model-f16.gguf')))
    print(agent.chain(INITIAL_PROMPT, Path('./images/NY.png')))