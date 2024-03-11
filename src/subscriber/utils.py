from . import SIOSubscriber, SQLiteSubscriber, MultiSubscriber


def default_subscriber(sio=None):
    return MultiSubscriber([SIOSubscriber(sio), SQLiteSubscriber()])
