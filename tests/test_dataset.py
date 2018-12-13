import unittest

from deep_speaker.features import label_from_path, set_from_path
from deep_speaker.dataset.split import pair_set


class DatasetTestCase(unittest.TestCase):
    def test_label_from_path(self):
        self.assertEqual(
            'id00017',
            label_from_path('/opt/dataset/voxceleb2/dev/aac/id00017/gjYcaCzo7UU/00111.m4a'))

    def test_train_set_from_path(self):
        self.assertEqual(
            'train',
            set_from_path('/opt/dataset/voxceleb2/dev/aac/id00017/gjYcaCzo7UU/00111.m4a'))

    def test_test_set_from_path(self):
        self.assertEqual(
            'test',
            set_from_path('/opt/dataset/voxceleb2/test/aac/id00017/gjYcaCzo7UU/00111.m4a'))

    def test_pair(self):
        self.assertEqual(
            [
                ({'file': 'A1', 'label': 'A'}, {'file': 'A2', 'label': 'A'}),
                ({'file': 'A1', 'label': 'A'}, {'file': 'A3', 'label': 'A'}),
                ({'file': 'A2', 'label': 'A'}, {'file': 'A3', 'label': 'A'}),
                ({'file': 'B1', 'label': 'B'}, {'file': 'B2', 'label': 'B'}),
                ({'file': 'A1', 'label': 'A'}, {'file': 'B1', 'label': 'B'}),
                ({'file': 'A1', 'label': 'A'}, {'file': 'B2', 'label': 'B'}),
                ({'file': 'A2', 'label': 'A'}, {'file': 'B1', 'label': 'B'}),
                ({'file': 'A2', 'label': 'A'}, {'file': 'B2', 'label': 'B'}),
            ],
            pair_set([
                {'file': 'A1', 'label': 'A'},
                {'file': 'A2', 'label': 'A'},
                {'file': 'B1', 'label': 'B'},
                {'file': 'B2', 'label': 'B'},
                {'file': 'A3', 'label': 'A'},
            ])
        )
