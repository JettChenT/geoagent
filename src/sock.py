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
