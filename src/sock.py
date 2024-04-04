import asyncio
import io

import socketio
from aiohttp import web
from threading import Thread
from PIL import Image

from . import utils
from urllib.request import urlopen
from .subscriber import SIOSubscriber, default_subscriber
from .connector.gptv import Gpt4Vision
from .connector.fast_lm import Gpt35
from .agent import Agent
from .config import *
from .feeder import process_url

sio = socketio.AsyncServer(
    cors_allowed_origins='*',
    max_http_buffer_size=1e9
)
sio.instrument(auth={
    'username': 'admin',
    'password': os.environ['ADMIN_PASSWORD'],
})
app = web.Application()
sio.attach(app)

@sio.event
def connect(sid, environ):
    print("connect ", sid)

@sio.event
def disconnect(sid):
    print("disconnect ", sid)

@sio.on("start_session")
def start_session(sid, data):
    try:
        img_b64 = data['img_b64']
        with urlopen(img_b64) as response:
            img_b64 = response.read()
        description = data['description'] if 'description' in data else ""
        agent = Agent(Gpt4Vision(), subscriber=default_subscriber(sio))
        ses = agent.session
        utils.setup_session(ses)
        a_path = "run/user_upload.png" # TODO: fix this to be session specific
        im = Image.open(io.BytesIO(img_b64))
        im.save(a_path)
        th = Thread(target=agent.lats, args=(agent.image_pmpt(a_path, description), True))
        th.start()
        return ses.id
    except Exception as e:
        print(e)
        asyncio.run(sio.emit("error", str(e), room=sid))
        return

@sio.on("from_social")
def from_social(sid, data):
    sub = default_subscriber(sio)
    try:
        url = data['url']
        agent = Agent(Gpt4Vision(debug=True), subscriber=sub, fast_lm=Gpt35(debug=True))
        ses = agent.session
        utils.setup_session(ses)
        sub.push("set_session_info_key", (ses.id, "status", "Processing social media url..."))
        prompt = process_url(ses, url)
        sub.push("set_session_info_key", (ses.id, "status", "Social media url processed."))
        sub.push("url_processed", (url))
        th = Thread(target=agent.lats, args=(prompt, True))
        th.start()
        return ses.id
    except Exception as e:
        print(e)
        sub.push("error", str(e))
        return

app.router.add_static('/run', 'run')
app.router.add_static('/images', 'images')
app.router.add_static('/datasets', 'datasets')

def run_srv():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, 'localhost', 3141)
    loop.run_until_complete(site.start())
    loop.run_forever()

def start_srv():
    srv_thread = Thread(target=run_srv)
    srv_thread.start()
    return sio, srv_thread

if __name__ == '__main__':
    sio, srv_thread = start_srv()
    sio_sub = SIOSubscriber(sio)
    input("Press Enter to start...")
    input("Press Enter to stop...")
    srv_thread.join()


