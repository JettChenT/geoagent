from pathlib import Path
from PIL import Image
import time
from websocket_server import WebsocketServer

class VLLM:
    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        pass

    def heartbeat(self) -> bool:
        pass

class GPT4Vision(VLLM):
    WS_PORT = 8181

    def __init__(self):
        self.server = WebsocketServer(host='127.0.0.1', port=self.WS_PORT)
        self.server.set_fn_new_client(self.new_client)
        self.server.run_forever(True)
        self.server.set_fn_message_received(self.recv_incoming)
        self.incoming = []

    def new_client(self, _client, _server):
        print("new join!")

    def recv_incoming(self, _client, _server, message):
        if message != "undefined":
            self.incoming.append(message)

    def heartbeat(self) -> bool:
        return True

    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        if not self.heartbeat():
            raise ConnectionRefusedError()
        self.server.send_message_to_all(prompt + '\n')
        while len(self.incoming) == 0:
            time.sleep(0.1)
        return self.incoming.pop(0)

# test
if __name__ == '__main__':
    gv = GPT4Vision()
    while not gv.heartbeat():
        time.sleep(0.1)
    while True:
        inp = input()
        if inp == 'q':
            break
        print("RESULT", gv.prompt(inp))