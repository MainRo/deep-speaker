from collections import namedtuple
import unittest
import json
from rx import Observable
from rx.subjects import Subject
import deep_speaker.config as config
import cyclotron_std.io.file as file


def dict_to_namedtuple(obj):
    return namedtuple('x', obj.keys())(**obj)


class ConfigTestCase(unittest.TestCase):
    def test_base(self):
        # test expectations
        expected_file_request = file.Read(
            id='config',
            path='/foo/config.json',
            size=-1, mode='r')

        # test setup
        file_response = Subject()
        argv = Subject()

        sink = config.read_configuration(config.Source(
            file_response=file_response,
            argv=argv
        ))

        configuration = None
        file_request = None

        def config_on_next(i):
            nonlocal configuration
            configuration = i

        def file_request_on_next(i):
            nonlocal file_request
            file_request = i

        sink.configuration.subscribe(
            on_next=config_on_next
        )
        sink.file_request.subscribe(
            on_next=file_request_on_next
        )

        # feed source observables
        argv.on_next('theexe')
        argv.on_next('--config')
        argv.on_next('/foo/config.json')
        argv.on_completed()
        self.assertEqual(expected_file_request, file_request)

        file_response.on_next(
            file.ReadResponse(
                id='config',
                path='/foo/config.json',
                data=Observable.just('{ "foo": "bar"}'))
        )

        self.assertEqual(dict_to_namedtuple({"foo": "bar"}), configuration)

    def test_bad_json(self):
        # test expectations
        expected_file_request = file.Read(
            id='config',
            path='/foo/config.json',
            size=-1, mode='r')

        # test setup
        file_response = Subject()
        argv = Subject()

        sink = config.read_configuration(config.Source(
            file_response=file_response,
            argv=argv
        ))

        configuration = None
        configuration_error = None
        file_request = None

        def config_on_next(i):
            nonlocal configuration
            configuration = i

        def config_on_error(e):
            nonlocal configuration_error
            configuration_error = e

        def file_request_on_next(i):
            nonlocal file_request
            file_request = i

        sink.configuration.subscribe(
            on_next=config_on_next,
            on_error=config_on_error
        )
        sink.file_request.subscribe(
            on_next=file_request_on_next
        )

        # feed source observables
        argv.on_next('theexe')
        argv.on_next('--config')
        argv.on_next('/foo/config.json')
        argv.on_completed()
        self.assertEqual(expected_file_request, file_request)

        file_response.on_next(
            file.ReadResponse(
                id='config',
                path='/foo/config.json',
                data=Observable.just('{ "foo": bar}'))
        )

        self.assertIsInstance(
            configuration_error,
            json.decoder.JSONDecodeError)
