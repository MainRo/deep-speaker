from collections import namedtuple
import deep_speaker.config as config
import threading

from rx import Observable
from rx.subjects import Subject
from rx.concurrency import ThreadPoolScheduler
from deep_speaker.toolbox.asyncioscheduler import AsyncIOScheduler

from cyclotron.debug import TraceObserver
import cyclotron.router as router
import cyclotron_std.io.file as file

import deep_speaker.toolbox.audio_codec as audio_codec

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


def make_path_processor(file_response, feature_response):
    sink_request = Subject()
    feature_request = Subject()

    def process(path, configuration):
        ''' compute features for all files in path
        This lettable operator processes all files present in the path observable.
        It reads each file, process them, and writes the result. The processing
        is multithreaded via a thread pool. The resulting observable is still
        scheduled in the asyncio event loop.
        '''
        aio_ts_scheduler = AsyncIOScheduler(threadsafe=True)
        aio_scheduler = AsyncIOScheduler()
        thread_scheduler = ThreadPoolScheduler(
            max_workers=configuration.data_preparation.cpu_core_count)

        # prepare file routing : read media and write features
        media_file_response = file_response
        feature_write_request, write_feature_file = router.make_crossroad_router(feature_response)
        media_read_request, read_media_file = router.make_crossroad_router(media_file_response)

        media_read_request \
            .flat_map(lambda i: Observable.just(i, scheduler=thread_scheduler)) \
            .subscribe(sink_request)

        feature_write_request.subscribe(feature_request)

        # feature engineering
        return (
            path
            #.do_action(TraceObserver(prefix='write1', trace_next_payload=False))
            .flat_map(
                lambda i: i.files
                .map(lambda path: file.Read(
                    id='read_media',
                    path=path,
                    mode='rb',
                ))
                .let(read_media_file)
                .filter(lambda i: i.id == 'read_media')
                .flat_map(lambda media: media.data
                    #.do_action(lambda i: print('write20-{}'.format(threading.get_ident()))) \
                    #.do_action(TraceObserver(prefix='write20', trace_next_payload=False))
                    .let(process_audio, configuration=configuration.features)

                    .map(lambda i: data_to_feature(i, media.path, configuration))
                    #.do_action(TraceObserver(prefix='write21-{}'.format(threading.get_ident()), trace_next_payload=False))
                    # .do_action(lambda i: print(i.path))
                )
                #)
                #.do_action(lambda i: print('write2-{}'.format(threading.get_ident()))) \
                #.do_action(TraceObserver(prefix='write2', trace_next_payload=False))
            )
            # write feature file to disk
            .map(lambda i: file.Write(
               id='write_feature',
               path=i.path, data=i.data,
               mode='wb', mkdirs=True))
            .let(write_feature_file)
            .filter(lambda i: i.id == 'write_feature')
            .map(lambda i: i.path)

            #.do_action(lambda i: print('write2-2-{}'.format(threading.get_ident()))) \
            #.do_action(TraceObserver(prefix='write2-2', trace_next_payload=False))
            .observe_on(aio_ts_scheduler)
            #.map(lambda i: "/foo/bar/i/4.mp3")
            #.do_action(lambda i: print('write3-{}'.format(threading.get_ident())))
            #.do_action(TraceObserver(prefix='write3', trace_next_payload=False))
        )

    return sink_request, feature_request, process
