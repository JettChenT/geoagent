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
from .agent import Agent
from .config import *

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
        a_path = "run/user_upload.png"
        im = Image.open(io.BytesIO(img_b64))
        im.save(a_path)
        th = Thread(target=agent.lats, args=(str(a_path), description, True))
        th.start()
        return ses.id
    except Exception as e:
        print(e)
        asyncio.run(sio.emit("error", str(e), room=sid))
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
    sio_sub.push('global_info_set', ("b", "est"))
    sio_sub.push('set_session_info_key', ("a","wow", "something different"))
    sio_sub.push('global_info_set', ("test", "test"))
    sio_sub.push('set_session_info_key', ("test", "wowow", "something lovely"))
    input("Press Enter to stop...")


