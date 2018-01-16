import unittest
from nt.database import JsonDatabase
from nt.database import DictDatabase
from pathlib import Path
import shutil
import tempfile
from nt.io import dump_json


class ReaderTest(unittest.TestCase):
    def setUp(self):
        self.json = dict(
            datasets=dict(
                train=dict(
                    a=dict(example_id='a'),
                    b=dict(example_id='b')
                ),
                test=dict(
                    c=dict(example_id='c')
                )
            ),
            meta=dict()
        )
        # self.temp_directory = Path(tempfile.mkdtemp())
        # self.json_path = self.temp_directory / 'db.json'
        # dump_json(self.json, self.json_path)
        self.db = DictDatabase(self.json)

    def test_dataset_names(self):
        self.assertListEqual(
            self.db.dataset_names,
            list(self.json['datasets'].keys())
        )  # fails because dump_json sorts keys

    def test_iterator(self):
        iterator = self.db.get_iterator_by_names('train')
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            list(self.json['datasets']['train'].keys())
        )
        _ = iterator['a']
        _ = iterator['b']
        _ = iterator[0]
        _ = iterator[1]
        _ = iterator[:1][0]

    def test_map_iterator(self):
        iterator = self.db.get_iterator_by_names('train')

        def map_fn(d):
            d['example_id'] = d['example_id'].upper()
            return d

        iterator = iterator.map(map_fn)
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            'A B'.split()
        )
        _ = iterator['a']
        _ = iterator[0]
        _ = iterator[:1][0]

    def test_filter_iterator(self):
        iterator = self.db.get_iterator_by_names('train')

        def filter_fn(d):
            return not d['example_id'] == 'b'

        iterator = iterator.filter(filter_fn)
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            'a'.split()
        )
        _ = iterator['a']
        with self.assertRaises(IndexError):
            _ = iterator['b']
        with self.assertRaises(AssertionError):
            _ = iterator[0]
        with self.assertRaises(AssertionError):
            _ = iterator[:1]

    def test_concatenate_iterator(self):
        train_iterator = self.db.get_iterator_by_names('train')
        test_iterator = self.db.get_iterator_by_names('test')
        iterator = train_iterator.concatenate(test_iterator)
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            'a b c'.split()
        )
        self.assertEqual(
            iterator['a']['example_id'],
            'a'
        )
        self.assertEqual(
            iterator[0]['example_id'],
            'a'
        )
        _ = iterator[:1][0]

    def test_concatenate_iterator_double_keys(self):
        train_iterator = self.db.get_iterator_by_names('train')
        iterator = train_iterator.concatenate(train_iterator)
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            'a b a b'.split()
        )
        with self.assertRaises(AssertionError):
            _ = iterator['a']
        self.assertEqual(
            iterator[0]['example_id'],
            'a'
        )
        _ = iterator[:1][0]

    def test_multiple_concatenate_iterator(self):
        train_iterator = self.db.get_iterator_by_names('train')
        iterator = train_iterator.concatenate(train_iterator)
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            'a b a b'.split()
        )
        _ = iterator[:1][0]

    def test_slice_iterator(self):
        base_iterator = self.db.get_iterator_by_names('train')
        base_iterator = base_iterator.concatenate(base_iterator)
        iterator = base_iterator[:4]
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            'a b a b'.split()
        )
        iterator = base_iterator[:3]
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            'a b a'.split()
        )
        iterator = base_iterator[:5]  # Should this work?
        example_ids = [e['example_id'] for e in iterator]
        self.assertListEqual(
            example_ids,
            'a b a b'.split()
        )
        _ = base_iterator[:2]
        _ = base_iterator[:1]
        _ = base_iterator[:0]  # Should this work?

    # def tearDown(self):
    #     shutil.rmtree(str(self.temp_directory))


class UniqueIDReaderTest(unittest.TestCase):
    def setUp(self):
        self.d = dict(
            datasets=dict(
                train=dict(
                    a=dict(example_id='a'),
                    b=dict(example_id='b')
                ),
                test=dict(
                    a=dict(example_id='a')
                )
            ),
            meta=dict()
        )
        self.db = DictDatabase(self.d)

    def test_duplicate_id(self):
        with self.assertRaises(AssertionError):
            _ = self.db.get_iterator_by_names('train test'.split())

    def test_duplicate_id_with_prepend_dataset_name(self):
        _ = self.db.get_iterator_by_names('train test'.split(), prepend_dataset_name=True)