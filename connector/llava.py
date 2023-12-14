import array
import io
from pathlib import Path

from PIL import Image
from llama_cpp import Llama
from llama_cpp.llava_cpp import clip_model_load, llava_image_embed_make_with_bytes, llava_eval_image_embed, \
    llava_image_embed_free
from objc._bridgesupport import ctypes

import prompting
from connector import VLLM


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

    def load_image_path_embded(self, image: Path):
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

    def load_image_embed(self, image: Image.Image):
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
