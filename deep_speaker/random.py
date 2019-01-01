from collections import namedtuple
from rx import Observable

from cyclotron import Component
import random

Sink = namedtuple('Sink', ['request'])
Source = namedtuple('Source', ['response'])

# Sink items
SetSeed = namedtuple('SetSeed', ['value'])
Shuffle = namedtuple('Shuffle', ['id', 'data'])

# Source items
ShuffleResponse = namedtuple('ShuffleResponse', ['id', 'data'])


def make_driver():
    def driver(sink):
        def on_subscribe(observer):
            def on_next(i):
                if type(i) is SetSeed:
                    random.seed(i.value)
                elif type(i) is Shuffle:
                    data = list(i.data)
                    random.shuffle(data)
                    observer.on_next(ShuffleResponse(
                        id=i.id,
                        data=data
                    ))
                else:
                    observer.on_error("unknown item: {}".format(i))

            sink.request.subscribe(
                on_next=on_next,
                on_error=observer.on_error,
                on_completed=observer.on_completed,
            )
        return Source(
            response=Observable.create(on_subscribe)
        )

    return Component(call=driver, input=Sink)
