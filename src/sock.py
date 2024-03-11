import asyncio

import socketio
from aiohttp import web
from threading import Thread

from .subscriber import SIOSubscriber, default_subscriber
from .connector.gptv import Gpt4Vision
from .session import Session
from .agent import Agent
from .config import *

sio = socketio.AsyncServer(cors_allowed_origins='*')
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
        image_url = data['image_url']
        description = data['description'] if 'description' in data else ""
        agent = Agent(Gpt4Vision(), subscriber=default_subscriber(sio))
        ses = agent.session
        th = Thread(target=agent.lats, args=(image_url, description))
        th.start()
        return ses.id
    except Exception as e:
        sio.emit("error", str(e), room=sid)
        return


app.router.add_static('/run', 'run')
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


