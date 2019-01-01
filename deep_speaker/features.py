from collections import namedtuple
import deep_speaker.config as config
import threading
import json

from rx import Observable
from rx.concurrency import ThreadPoolScheduler
from .toolbox.asyncioscheduler import AsyncIOScheduler

from cyclotron.debug import TraceObserver
import cyclotron.router as router
import cyclotron_std.logging as logging
import cyclotron_std.os.walk as walk
import cyclotron_std.io.file as file
import cyclotron_aio.stop as stop
import deep_speaker.random as random

import deep_speaker.feature.process_path as path_processor
from deep_speaker.dataset.split import train_test_split, test_dev_split, pair_set


Source = namedtuple('Source', ['logging', 'feature_file', 'media_file', 'dataset_file', 'file', 'walk', 'random', 'argv'])
Sink = namedtuple('Sink', ['logging', 'feature_file', 'media_file', 'dataset_file', 'file', 'walk', 'stop', 'random'])


def label_from_path(filename):
    parts = filename.split('/')
    return parts[-3]


def set_from_path(filename):
    parts = filename.split('/')
    return 'train' if parts[-5] == 'dev' else 'test'


def extract_features(sources):
    aio_scheduler = AsyncIOScheduler()
    file_response = sources.file.response.share()
    config_sink = config.read_configuration(config.Source(
        file_response=file_response,
        argv=sources.argv.argv.subscribe_on(aio_scheduler)
    ))
    configuration = config_sink.configuration.share()

    walk_adapter = walk.adapter(sources.walk.response)
    #file_adapter = file.adapter(sources.media_file.response)
    #write_feature_request, write_feature_file = router.make_crossroad_router(file_response)
    media_file_request, feature_file_request, process_path = path_processor.make_path_processor(sources.media_file.response, sources.feature_file.response)
    random_cross_request, cross_random = router.make_crossroad_router(sources.random.response)

    features = (
        configuration
        .flat_map(lambda configuration: walk_adapter.api.walk(
            configuration.dataset.voxceleb2_path)
            # extract features from files
            .let(process_path,
                 configuration=configuration,
                 #file_adapter=file_adapter,
                )
            # create sets
            .reduce(
                lambda acc, i: acc + [{
                    'file': i, 
                    'label': label_from_path(i),
                    'set': set_from_path(i),
                }],
                seed=[])
            # todo: shuffle
            .map(train_test_split)
            .flat_map(lambda dataset: Observable.just(dataset['test'])
                .map(pair_set)
                # shuffle apn pairs
                .map(lambda i: random.Shuffle(id='dev_test_set', data=i))
                .let(cross_random)
                .filter(lambda i: i.id == 'dev_test_set')
                .map(lambda i: i.data)

                .map(lambda i: test_dev_split(i,
                    configuration.dataset.dev_set_utterance_count,
                    configuration.dataset.test_set_utterance_count))
                .map(lambda i: {
                    'train': dataset['train'],
                    'dev': i['dev'],
                    'test': i['test'],
                })
            )
        )
        .share()
    )

    # save dataset json file
    write_dataset_request = (
        features
        .map(json.dumps)
        .with_latest_from(configuration, lambda dataset, configuration:  file.Write(
               id='write_dataset',
               path=configuration.dataset.path, data=dataset,
               mode='w')
        )
        .share()
    )

    # random
    random_request = Observable.concat(
        configuration.map(lambda i: random.SetSeed(value=i.random_seed)),
        random_cross_request)

    logs = features
    exit = sources.dataset_file.response.ignore_elements()

    return Sink(
        file=file.Sink(request=config_sink.file_request),
        dataset_file=file.Sink(request=write_dataset_request),
        media_file=file.Sink(request=media_file_request),
        feature_file=file.Sink(request=feature_file_request),
        logging=logging.Sink(request=logs),
        walk=walk.Sink(request=walk_adapter.sink),
        stop=stop.Sink(control=exit),
        random=random.Sink(request=random_request)
    )
