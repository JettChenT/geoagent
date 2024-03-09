from threading import Thread
from typing import List


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