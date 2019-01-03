from collections import namedtuple
from rx import Observable

from cyclotron import Component

Sink = namedtuple('Sink', ['request'])
Source = namedtuple('Source', ['response'])

# Sink events
Initialize = namedtuple('Initialize', ['dataset', 'config'])

# Source events
Train = namedtuple('Train', [])
Test = namedtuple('Test', [])
Eval = namedtuple('Eval', [])


def schedule(config, observer):
    return


def make_driver():
    def driver(sink):
        def on_subscribe(observer):
            def on_next(i):
                if type(i) is Initialize:
                    print("init: {}".format(i))
                    schedule(i, observer)
                else:
                    observer.on_error("scheduler unknown command: {}".format(i))

            sink.request.subscribe(
                on_next=on_next,
                on_error=observer.on_error,
                on_completed=observer.on_completed,
            )

        return Source(
            response=Observable.create(on_subscribe)
        )

    return Component(call=driver, input=Sink)
