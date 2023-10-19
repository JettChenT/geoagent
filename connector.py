from pathlib import Path
from PIL import Image
import time
from websocket_server import WebsocketServer
import requests
import io

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


class LLAVA(VLLM):
    def __init__(self, endpoint="http://localhost:8080"):
        self.endpoint = endpoint

    def heartbeat(self) -> bool:
        return requests.get(self.endpoint).status_code == 200

    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        files = None
        if image is not None:
            if isinstance(image, Path):
                files = {'image_file': open(image, 'rb')}
            elif isinstance(Image.Image):
                output = io.BytesIO()
                image.save(output, format='JPEG')
                files = {"image_file": output}
        r = requests.post(f"{self.endpoint}/llava", data={"user_prompt": prompt}, files=files)
        return r.json()['content']

# test
if __name__ == '__main__':
    llava = LLAVA()
    print(llava.prompt("Describe this image", Path(__file__).parent/"images"/"NY.png"))