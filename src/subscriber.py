from enum import Enum
from typing import List
from threading import Thread
import asyncio
import socketio


class Subscriber:
    def push(self, msg_type, msg):
        pass


class MultiSubscriber(Subscriber):
    def __init__(self, subscribers: List[Subscriber]):
        self.subscribers = subscribers

    def push(self, msg_type, msg):
        tasks = []
        for sub in self.subscribers:
            t = Thread(target=sub.push, args=(msg_type, msg))
            tasks.append(t)
            t.start()
        for t in tasks:
            t.join()


class SIOSubscriber(Subscriber):
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio

    def push(self, msg_type, msg):
        print(f"pushing message {msg_type}, {hash(str(msg))} to sio")
        asyncio.run(self.sio.emit(msg_type, msg))
        print(f"pushed message {msg_type}, {hash(str(msg))} to sio")
