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
import deep_speaker.training.trainer as trainer


LoadDatasetSource = namedtuple('LoadDatasetSource', ['file_response', 'path'])
LoadDatasetSink = namedtuple('LoadDatasetSink', ['file_request', 'dataset'])


def load_dataset(source):
    read_request = Observable.just(
    file.Context(id='dataset', observable=source.path
        .map(lambda i: file.Read(id='dataset', path=i)))
    )

    dataset = (
        source.file_response
        .filter(lambda i: i.id == "dataset")
        .flat_map(lambda i: i.observable)
        .flat_map(lambda i: i.data)
    )

    return LoadDatasetSink(
        file_request=read_request,
        dataset=dataset
    )


Source = namedtuple('Source', ['trainer', 'logging', 'file', 'argv'])
Sink = namedtuple('Sink', ['trainer', 'logging', 'file', 'stop'])


def train(sources):
    aio_scheduler = AsyncIOScheduler()
    file_response = sources.file.response.share()
    config_sink = config.read_configuration(config.Source(
        file_response=file_response,
        argv=sources.argv.argv.subscribe_on(aio_scheduler)
    ))
    config_data = config_sink.configuration.share()

    # load dataset
    dataset = load_dataset(LoadDatasetSource(
        file_response=file_response,
        path=config_data.map(lambda i: i.dataset.path)
    ))

    # schedule training
    scheduler_init = Observable.zip(dataset.dataset, config_data,
        lambda dataset, config: scheduler.Schedule(dataset, config.train))

    scheduler_sink = scheduler.schedule(
        scheduler.Source(feedback=scheduler_init)
    )

    # load batch

    # train/eval/save model
    trainer_init = config_data.map(lambda i: trainer.Initialize(
        optimizer=i.train.settings.optimizer,
        loss=i.train.settings.loss,
    ))
    trainer_requests = scheduler_sink.command

    logs = sources.trainer.response
    exit = Observable.never() # config_data.ignore_elements()

    return Sink(
        trainer=trainer.Sink(request=Observable.merge(
            trainer_init,
            trainer_requests
        )),
        file=file.Sink(request=Observable.merge(
            config_sink.file_request,
            dataset.file_request,
        )),
        logging=logging.Sink(request=logs),
        stop=stop.Sink(control=exit),
    )
