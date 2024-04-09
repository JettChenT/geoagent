from . import Subscriber
from typing import Optional
import socketio
import asyncio
from .subscriber_message import SubscriberMessageType

class SIOSubscriber(Subscriber):
    def __init__(self, sio: Optional[socketio.AsyncServer] = None):
        if sio is None:
            from ..sock import start_srv
            sio, sub_thread = start_srv()
        self.sio = sio

    def push(self, msg_type: SubscriberMessageType, msg):
        asyncio.run(self.sio.emit(msg_type.value, msg))
