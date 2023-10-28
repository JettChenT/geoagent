from pathlib import Path
from PIL import Image
from websocket_server import WebsocketServer
import requests
import io
import array
import ctypes
import asyncio
from llama_cpp import (
    Llama,
    clip_model_load,
    llava_image_embed_make_with_bytes,
    llava_image_embed_p,
    llava_image_embed_free,
    llava_eval_image_embed,
)
from utils import md
import prompting


class VLLM:
    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        pass

    def heartbeat(self) -> bool:
        pass


class GPT4Vision(VLLM):
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
        if (
            message != "undefined"
            and message is not None
            and isinstance(message, str)
            and len(message) > 40
        ):
            print("appending message")
            self.incoming.append(md(message))

    async def wait_for_message(self):
        while len(self.incoming) == 0:
            await asyncio.sleep(0.01)
        return self.incoming.pop(0)

    def heartbeat(self) -> bool:
        return True

    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        if image is not None:
            print(
                "Automatic Image Upload not supported yet. Please upload the image manually."
            )
            print(f"The image is located at {image}")
            input("Press Enter to continue...")
        if not self.heartbeat():
            raise ConnectionRefusedError()
        self.server.send_message_to_all(prompt + "\n")
        return asyncio.run(self.wait_for_message())


class LLAVA_Server(VLLM):
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


class LLAVA(VLLM):
    """
    LLAMA CPP Based LLAVA implementation
    TODO: try using StreetCLIP for embedding
    """

    MAX_TARGET_LEN = 256
    N_CTX = 2048

    def __init__(self, model: Path, mmproj: Path, temp: float = 0.1):
        self.temp = temp
        self.llm = Llama(model_path=str(model), n_ctx=self.N_CTX, n_gpu_layers=1)
        self.ctx_clip = clip_model_load(str(mmproj).encode("utf-8"))
        self.system_prompt()

    def load_image_path_embded(self, image: Path) -> llava_image_embed_p:
        with open(image, "rb") as file:
            image_bytes = file.read()
            bytes_length = len(image_bytes)
            data_array = array.array("B", image_bytes)
            c_ubyte_ptr = (ctypes.c_ubyte * len(data_array)).from_buffer(data_array)
        return llava_image_embed_make_with_bytes(
            ctx_clip=self.ctx_clip,
            n_threads=1,
            image_bytes=c_ubyte_ptr,
            image_bytes_length=bytes_length,
        )

    def load_image_embed(self, image: Image.Image) -> llava_image_embed_p:
        output = io.BytesIO()
        image.save(output, format="PNG")
        im_len = len(output.getvalue())
        data_array = array.array("B", output.getvalue())
        c_ubyte_ptr = (ctypes.c_ubyte * len(data_array)).from_buffer(data_array)
        return llava_image_embed_make_with_bytes(
            ctx_clip=self.ctx_clip,
            n_threads=1,
            image_bytes=c_ubyte_ptr,
            image_bytes_length=im_len,
        )

    def eval_img(self, image: Image.Image | Path):
        if isinstance(image, Image.Image):
            im = self.load_image_embed(image)
        else:
            im = self.load_image_path_embded(image)
        n_past = ctypes.c_int(self.llm.n_tokens)
        n_past_p = ctypes.byref(n_past)
        llava_eval_image_embed(self.llm.ctx, im, self.llm.n_batch, n_past_p)
        self.llm.n_tokens = n_past.value
        llava_image_embed_free(im)

    def output(self, stream=True):
        res = ""
        for i in range(self.MAX_TARGET_LEN):
            t_id = self.llm.sample(temp=self.temp)
            t = self.llm.detokenize([t_id]).decode("utf8")
            if t == "</s>":
                break
            if stream:
                print(t, end="")
            res += t
            self.llm.eval([t_id])
        return res

    def system_prompt(self):
        self.llm.eval(self.llm.tokenize(prompting.LLAVA_SYS_PROMPT.encode("utf8")))

    def prompt(self, prompt: str, image: Image.Image | Path | None = None) -> str:
        self.llm.eval(self.llm.tokenize("\nUSER: ".encode("utf8")))
        if image is not None:
            self.eval_img(image)
        self.llm.eval(self.llm.tokenize(prompt.encode("utf8")))
        self.llm.eval(self.llm.tokenize("\nASSISTANT:".encode("utf8")))
        return self.output()

    def heartbeat(self) -> bool:
        return self.llm is not None


def test_llava():
    llava_folder = Path(__file__).parent.parent / "models" / "llava"
    llava = LLAVA(
        llava_folder / "ggml-model-q4_k.gguf", llava_folder / "mmproj-model-f16.gguf"
    )
    _res = llava.prompt("Hi there! How are you?")


def test_gpt_connection():
    gpt = GPT4Vision()
    input("enter to start...")
    print(
        f"---RESULT\n{gpt.prompt('output a python implementation of hello world with 10 lines')}"
    )


# test
if __name__ == "__main__":
    # test_gpt_connection()
    test_llava()
