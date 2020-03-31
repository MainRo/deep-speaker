from collections import namedtuple
import numpy as np
import rx.operators as ops
import rxsci as rs
from rxsci.io.file import read
from cyclotron.debug import trace_observable

import deep_speaker.toolbox.audio_codec as audio_codec
from deep_speaker.toolbox.audio_features import compute_mfcc

Feature = namedtuple('Feature', ['label', 'data'])


def label_from_path(filename):
    parts = filename.split('/')
    label = parts[-3]
    label = int(label[2:])
    return label


def set_from_path(filename):
    parts = filename.split('/')
    return 'train' if parts[-5] == 'dev' else 'test'


def process_audio(data):
    return data.pipe(
        ops.map(audio_codec.decode_audio),
        ops.map(audio_codec.encode_wav),
        ops.map(lambda i: np.frombuffer(i, dtype=np.int16)),
        ops.map(lambda i: i[0:16000]),
        ops.do_action(lambda i: print(len(i))),
        ops.map(compute_mfcc),
        ops.do_action(lambda i: print(len(i))),
    )


def translate_path(dataset_file, source_path, dest_path):
    ''' returns the feature file name from the dataset file name
    '''
    feature_file = dataset_file.replace(
        source_path,
        dest_path)
    feature_file = feature_file.replace('.m4a', '.bin')
    return feature_file


def compute_features(config, file):

    feature_utterance = file.pipe(
        trace_observable("utterance 1"),
        ops.flat_map(lambda file_path: read(file_path, mode='rb').pipe(
            trace_observable("utterance 2", trace_next_payload=False),
            process_audio,
            rs.with_latest_from(config),
            ops.starmap(lambda data, config: Feature(
                label=label_from_path(file_path),
                data=data)),
        )),
        trace_observable("utterance", trace_next_payload=False),
    )

    return feature_utterance,
