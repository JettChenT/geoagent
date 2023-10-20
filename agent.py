from connector import VLLM

class Agent:
    def __init__(self, vllm: VLLM):
        self.vllm = vllm

