import json
from collections import namedtuple
from rx import Observable
import cyclotron_std.argparse as argparse
import cyclotron_std.io.file as file


Source = namedtuple('Source', ['file_response', 'argv'])
Sink = namedtuple('Sink', ['file_request', 'configuration'])


def read_configuration(source):
    args = argparse.argparse(
        argv=source.argv.skip(1),
        parser=Observable.just(argparse.Parser(description="deepspeaker")),
        arguments=Observable.from_([
            argparse.ArgumentDef(
                name='--config', help="Path of the configuration file")
        ])
    )

    read_config_file = (
        args
        .filter(lambda i: i.key == 'config')
        .map(lambda i: file.Read(id='config', path=i.value))
    )

    config = (
        source.file_response
        .filter(lambda i: i.id == "config")
        .flat_map(lambda i: i.data)
        .map(lambda i: json.loads(
            i,
            object_hook=lambda d: namedtuple('x', d.keys())(*d.values())))
    )

    return Sink(
        file_request=read_config_file,
        configuration=config
    )
