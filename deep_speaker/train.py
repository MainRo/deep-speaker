from collections import namedtuple
import deep_speaker.config as config
import threading

from rx import Observable
from rx.concurrency import ThreadPoolScheduler
from .toolbox.asyncioscheduler import AsyncIOScheduler

from cyclotron.debug import TraceObserver
import cyclotron.router as router
import cyclotron_std.logging as logging
import cyclotron_std.io.file as file
import cyclotron_aio.stop as stop

import deep_speaker.training.scheduler as scheduler


Source = namedtuple('Source', ['scheduler', 'logging', 'file', 'argv'])
Sink = namedtuple('Sink', ['scheduler', 'logging', 'file', 'stop'])


LoadDatasetSource = namedtuple('LoadDatasetSource', ['path'])
LoadDatasetSink = namedtuple('LoadDatasetSink', ['dataset'])


def load_dataset(source):
    return LoadDatasetSink(dataset=Observable.just('foo'))


def train(sources):
    aio_scheduler = AsyncIOScheduler()
    file_response = sources.file.response.share()
    config_sink = config.read_configuration(config.Source(
        file_response=file_response,
        argv=sources.argv.argv.subscribe_on(aio_scheduler)
    ))
    config_data = config_sink.configuration.share()

    # load dataset
    dataset = load_dataset(LoadDatasetSource(path=config_data))

    # start scheduler
    scheduler_init = Observable.zip(dataset.dataset, config_data,
        lambda dataset, config: scheduler.Initialize(dataset, config.train))

    # load batch

    # train/eval/save model

    logs = sources.scheduler.response
    exit = Observable.empty() # config_data.ignore_elements()

    return Sink(
        scheduler=scheduler.Sink(request=scheduler_init),
        file=file.Sink(request=config_sink.file_request),
        logging=logging.Sink(request=logs),
        stop=stop.Sink(control=exit),
    )
