from collections import namedtuple
from rx import Observable

from cyclotron import Component

import deep_speaker.training as training

Sink = namedtuple('Sink', ['request'])
Source = namedtuple('Source', ['response'])

Initialize = namedtuple('Initialize', ['optimizer', 'loss'])


def make_driver():
    def driver(sink):
        def on_subscribe(observer):
            def on_next(i):
                if type(i) is training.TrainRequest:
                    print('Train')
                elif type(i) is training.TestRequest:
                    print('Test')
                elif type(i) is training.EvalRequest:
                    print('Eval')
                elif type(i) is Initialize:
                    print(i.optimizer)

            sink.request.subscribe(
                on_next=on_next,
                on_error=observer.on_error,
                on_completed=observer.on_completed,
            )

        return Source(
            response=Observable.create(on_subscribe)
        )

    return Component(call=driver, input=Sink)