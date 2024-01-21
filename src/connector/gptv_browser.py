# This should be considered deprecated

import asyncio
import io
import json
from pathlib import Path

import requests
from PIL import Image
from websocket_server import WebsocketServer

from ..utils import md, image_to_base64
from . import LMM

class GPT4VisionBrowser(LMM):
    """
    Connector to GPT4, based on a web browser api
    TODO: switch to selenium controller for file upload
    """

    WS_PORT = 8181

    def __init__(self):
        self.server = WebsocketServer(host="127.0.0.1", port=self.WS_PORT)
        self.server.set_fn_new_client(self.new_client)
        self.server.run_forever(True)
        self.server.set_fn_message_received(self.recv_incoming)
        self.incoming = []

    def new_client(self, _client, _server):
        print("new join!")

    def recv_incoming(self, _client, _server, message):
        print("received message:", message)
        try:
            msg_data = json.loads(message)
            if msg_data["type"] == "message" and msg_data["message"] and (md_conv:=md(msg_data["message"])):
                message = self.incoming.append(md_conv)
                self.incoming.append(message)
        except Exception:
            return

    async def wait_for_message(self):
        while len(self.incoming) == 0:
            await asyncio.sleep(0.01)
        return self.incoming.pop(0)

    def heartbeat(self) -> bool:
        return True

    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        send_dat = {"message": prompt}
        if image is not None:
            im = image if isinstance(image, Image.Image) else Image.open(image)
            send_dat["image"] = image_to_base64(im)
        if not self.heartbeat():
            raise ConnectionRefusedError()
        self.server.send_message_to_all(json.dumps(send_dat) + "\n")
        return asyncio.run(self.wait_for_message())


class LLAVA_Server(LMM):
    # TODO: implement context for LLAVA
    def __init__(self, endpoint="http://localhost:8080"):
        self.endpoint = endpoint

    def heartbeat(self) -> bool:
        return requests.get(self.endpoint).status_code == 200



    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        files = None
        if image is not None:
            if isinstance(image, Path):
                files = {"image_file": open(image, "rb")}
            elif isinstance(Image.Image):
                output = io.BytesIO()
                image.save(output, format="JPEG")
                files = {"image_file": output}
        r = requests.post(
            f"{self.endpoint}/llava", data={"user_prompt": prompt}, files=files
        )
        return r.json()["content"]