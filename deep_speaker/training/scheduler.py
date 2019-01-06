from collections import namedtuple
from rx import Observable

from cyclotron import Component

import deep_speaker.training as training

Sink = namedtuple('Sink', ['command'])
Source = namedtuple('Source', ['feedback'])

# Sink events
Schedule = namedtuple('Initialize', ['dataset', 'config'])

# Source events


def schedule(source):
    def on_subscribe(observer):
        def on_next(i):
            if type(i) is Schedule:
                # print("init: {}".format(i))
                observer.on_next(training.TrainRequest())
                # schedule(i, observer)
            else:
                observer.on_error("scheduler unknown command: {}".format(i))

        source.feedback.subscribe(
            on_next=on_next,
            on_error=observer.on_error,
            on_completed=observer.on_completed,
        )

    return Sink(
        command=Observable.create(on_subscribe)
    )
