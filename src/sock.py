import asyncio

import socketio
from aiohttp import web
from threading import Thread
import os
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

app.router.add_static('/run', 'run')

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
    from .subscriber import SIOSubscriber
    sio, srv_thread = start_srv()
    sio_sub = SIOSubscriber(sio)
    input("Press Enter to start...")
    sio_sub.push('global_info_set', ("b", "est"))
    sio_sub.push('set_session_info_key', ("a","wow", "something different"))
    sio_sub.push('global_info_set', ("test", "test"))
    sio_sub.push('set_session_info_key', ("test", "wowow", "something lovely"))
    input("Press Enter to stop...")


