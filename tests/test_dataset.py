import unittest

from deep_speaker.features import label_from_path, set_from_path


class DatasetTestCase(unittest.TestCase):
    def test_label_from_path(self):
        self.assertEqual(
            '00111',
            label_from_path('/opt/dataset/voxceleb2/dev/aac/id00017/gjYcaCzo7UU/00111.m4a'))

    def test_train_set_from_path(self):
        self.assertEqual(
            'train',
            set_from_path('/opt/dataset/voxceleb2/dev/aac/id00017/gjYcaCzo7UU/00111.m4a'))

    def test_test_set_from_path(self):
        self.assertEqual(
            'test',
            set_from_path('/opt/dataset/voxceleb2/test/aac/id00017/gjYcaCzo7UU/00111.m4a'))
