from collections import namedtuple
import deep_speaker.config as config

from rx.concurrency import AsyncIOScheduler

import cyclotron_std.logging as logging
import cyclotron_std.os.walk as walk
import cyclotron_std.io.file as file
import cyclotron.router as router

Source = namedtuple('Source', ['logging', 'file', 'walk', 'argv'])
Sink = namedtuple('Sink', ['logging', 'file', 'walk'])


def extract_features(sources):
    aio_scheduler = AsyncIOScheduler()
    config_sink = config.read_configuration(config.Source(
        file_response=sources.file.response,
        argv=sources.argv.argv.subscribe_on(aio_scheduler)
    ))

    configuration = config_sink.configuration
    walk_request, walk_directory = router.make_crossroad_router(sources.walk.response)

    features = (
        configuration
        .map(lambda i: i.dataset.voxceleb2_path)
        .do_action(lambda i: print(i))
        .let(walk_directory)
        .do_action(lambda i: print(i))
        # .flat_map()
        # .observe_on()
        .map(lambda i: file.Write())
    )

    logs = features

    return Sink(
        file=file.Sink(request=config_sink.file_request),
        logging=logging.Sink(request=logs),
        walk=walk.Sink(request=walk_request),
    )
