import rx
import rx.operators as ops
import rxsci as rs
from rxsci.io.walk import walk
from cyclotron.debug import trace_observable


def list_files(config, dataset_key='voxceleb2_test_path'):

    files = rx.just(None).pipe(
        rs.with_latest_from(config),
        ops.starmap(lambda _, c: walk(c['config']['dataset'][dataset_key])),
        ops.merge_all(),
    )

    return files,


def list_train_files(config):
    train_files, = list_files(config, dataset_key='voxceleb2_train_path')

    train, val = train_files.pipe(
        rs.train_test_split(0.01, sampling_size=2),
    )

    print("train: {}, val: {}".format(train, val))
    return train, val
