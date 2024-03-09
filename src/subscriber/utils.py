from . import SIOSubscriber, SQLiteSubscriber, MultiSubscriber


def default_subscriber():
    return MultiSubscriber([SIOSubscriber(), SQLiteSubscriber()])
