import rx
import rx.operators as ops
import rxsci as rs
from rxsci.io.walk import walk
from cyclotron.debug import trace_observable


def list_files(config):

    files = rx.just(None).pipe(
        rs.with_latest_from(config),
        ops.starmap(lambda _, c: walk(c['config']['dataset']['voxceleb2_path'])),
        ops.merge_all(),
        trace_observable("files"),
    )

    return files,
