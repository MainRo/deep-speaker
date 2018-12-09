from collections import namedtuple
import deep_speaker.config as config
import threading

from rx import Observable
from rx.concurrency import ThreadPoolScheduler
from .toolbox.asyncioscheduler import AsyncIOScheduler

from cyclotron.debug import TraceObserver
import cyclotron_std.logging as logging
import cyclotron_std.os.walk as walk
import cyclotron_std.io.file as file
import cyclotron_aio.stop as stop

import deep_speaker.feature.process_path as path_processor


Source = namedtuple('Source', ['logging', 'feature_file', 'media_file', 'file', 'walk', 'argv'])
Sink = namedtuple('Sink', ['logging', 'feature_file', 'media_file', 'file', 'walk', 'stop'])


def label_from_path(filename):
    parts = filename.split('/')
    return parts[-1]


def extract_features(sources):
    aio_scheduler = AsyncIOScheduler()
    file_response = sources.file.response.share()
    config_sink = config.read_configuration(config.Source(
        file_response=file_response,
        argv=sources.argv.argv.subscribe_on(aio_scheduler)
    ))

    walk_adapter = walk.adapter(sources.walk.response)
    #file_adapter = file.adapter(sources.media_file.response)
    #write_feature_request, write_feature_file = router.make_crossroad_router(file_response)
    media_file_request, feature_file_request, process_path = path_processor.make_path_processor(sources.media_file.response, sources.feature_file.response)

    features = (
        config_sink.configuration
        .flat_map(lambda configuration: walk_adapter.api.walk(
            configuration.dataset.voxceleb2_path)
            # extract features from files
            .let(process_path,
                 configuration=configuration,
                 #file_adapter=file_adapter,
                )
            # create sets
            .reduce(
                lambda acc, i: acc + [{'file': i, 'label': label_from_path(i)}],
                seed=[])
            .do_action(TraceObserver(prefix='sets', trace_next_payload=False))
            # .do_action(lambda i: print("{}: {}".format(threading.get_ident(), i.status)))
        )
        .map(lambda i: "")
        .share()
    )

    logs = features

    exit = (
        features
        .ignore_elements()
    )

    return Sink(
        file=file.Sink(request=Observable.merge(
            config_sink.file_request,            
            #file_adapter.sink,
            #write_feature_request,
        )),
        media_file=file.Sink(request=media_file_request),
        feature_file=file.Sink(request=feature_file_request),
        logging=logging.Sink(request=logs),
        walk=walk.Sink(request=walk_adapter.sink),
        stop=stop.Sink(control=exit),
    )
