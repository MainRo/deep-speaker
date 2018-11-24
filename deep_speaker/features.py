from collections import namedtuple
import deep_speaker.config as config

from rx.concurrency import AsyncIOScheduler

from rx import Observable

from cyclotron.debug import TraceObserver
import cyclotron_std.logging as logging
import cyclotron_std.os.walk as walk
import cyclotron_std.io.file as file
import cyclotron.router as router

Source = namedtuple('Source', ['logging', 'file', 'walk', 'argv'])
Sink = namedtuple('Sink', ['logging', 'file', 'walk'])


def process_audio(data, configuration):
    #print(configuration)
    return (data
        # .do_action(lambda i: print(i))
    )


def write_features(data, source_file, configuration):
    sink_file = source_file.replace(
        configuration.dataset.voxceleb2_path,
        configuration.dataset.features_path)
    sink_file = sink_file.replace('.m4a', '.bin')
    return file.Write(id='feature_file', path=sink_file, data=data)


def extract_features(sources):
    aio_scheduler = AsyncIOScheduler()
    file_response = sources.file.response.share()
    config_sink = config.read_configuration(config.Source(
        file_response=file_response,
        argv=sources.argv.argv.subscribe_on(aio_scheduler)
    ))

    walk_adapter = walk.adapter(sources.walk.response)
    file_adapter = file.adapter(file_response)

    def list_files(path):
        return (path
            .map(lambda i: walk.Walk(top=i, id='voxceleb2', recursive=True))
            .let(walk_directory)
            .filter(lambda i: i.id == 'voxceleb2'))

    features = (
        config_sink.configuration
        .flat_map(lambda configuration: walk_adapter.api.walk(configuration.dataset.voxceleb2_path)
            .flat_map(lambda i: i.files
                .flat_map(lambda path: file_adapter.api.read(path, mode='rb')
                    .let(process_audio, configuration=configuration.features)
                    .map(lambda i: write_features(i, path, configuration))
                    .do_action(lambda i: print(i.path))
                    #.map(lambda i: file.Write())
                )
            )
            # .observe_on()
        )
        .map(lambda i: "")
    )

    logs = features

    return Sink(
        file=file.Sink(request=Observable.merge(
            config_sink.file_request,
            file_adapter.sink,
        )),
        logging=logging.Sink(request=logs),
        walk=walk.Sink(request=walk_adapter.sink.do_action(lambda i: print(i))),
    )
