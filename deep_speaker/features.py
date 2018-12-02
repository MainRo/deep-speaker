from collections import namedtuple
import deep_speaker.config as config
import threading

from rx import Observable
from rx.concurrency import ThreadPoolScheduler
from .toolbox.asyncioscheduler import AsyncIOScheduler

# from cyclotron.debug import TraceObserver
import cyclotron_std.logging as logging
import cyclotron_std.os.walk as walk
import cyclotron_std.io.file as file
import cyclotron.router as router

import deep_speaker.toolbox.audio_codec as audio_codec

Source = namedtuple('Source', ['logging', 'file', 'walk', 'argv'])
Sink = namedtuple('Sink', ['logging', 'file', 'walk'])


Feature = namedtuple('Feature', ['path', 'data'])


def process_audio(data, configuration):
    return (
        data
        .map(lambda i: audio_codec.decode_audio(i))
        .map(lambda i: audio_codec.encode_wav(i))
    )


def data_to_feature(data, source_file, configuration):
    sink_file = source_file.replace(
        configuration.dataset.voxceleb2_path,
        configuration.dataset.features_path)
    sink_file = sink_file.replace('.m4a', '.bin')
    return Feature(path=sink_file, data=data)


def process_path(path, configuration, write_feature_file, file_adapter):
    ''' compute features for all files in path
    This lettable operator processes all files present in the path observable.
    It reads each file, process them, and writes the result. The processing
    is multithreaded via a thread pool. The resulting observable is still
    scheduled in the asyncio event loop.
    '''
    aio_ts_scheduler = AsyncIOScheduler(threadsafe=True)
    thread_scheduler = ThreadPoolScheduler(
        max_workers=configuration.data_preparation.cpu_core_count)

    return (
        path
        .flat_map(
            lambda i: i.files
            .flat_map(
                lambda path: file_adapter.api.read(path, mode='rb')
                .subscribe_on(thread_scheduler)
                .do_action(lambda i: print(threading.get_ident()))
                .let(process_audio, configuration=configuration.features)
                .map(lambda i: data_to_feature(i, path, configuration))
                .do_action(lambda i: print(i.path))
            )
        )
        # write feature file to disk
        .map(lambda i: file.Write(
            id='feature',
            path=i.path, data=i.data,
            mode='wb', mkdirs=True))
        .let(write_feature_file)
        .filter(lambda i: i.id == 'feature')
        .observe_on(aio_ts_scheduler)
    )


def extract_features(sources):
    aio_scheduler = AsyncIOScheduler()
    file_response = sources.file.response.share()
    config_sink = config.read_configuration(config.Source(
        file_response=file_response,
        argv=sources.argv.argv.subscribe_on(aio_scheduler)
    ))

    walk_adapter = walk.adapter(sources.walk.response)
    file_adapter = file.adapter(file_response)
    write_feature_request, write_feature_file = router.make_crossroad_router(file_response)

    features = (
        config_sink.configuration
        .flat_map(lambda configuration: walk_adapter.api.walk(
            configuration.dataset.voxceleb2_path)
            .let(process_path,
                 configuration=configuration,
                 write_feature_file=write_feature_file,
                 file_adapter=file_adapter)
            .do_action(lambda i: print("{}: {}".format(threading.get_ident(), i.status)))
        )
        .map(lambda i: "")
    )

    logs = features

    return Sink(
        file=file.Sink(request=Observable.merge(
            config_sink.file_request,
            file_adapter.sink,
            write_feature_request,
        )),
        logging=logging.Sink(request=logs),
        walk=walk.Sink(request=walk_adapter.sink.do_action(lambda i: print(i))),
    )
