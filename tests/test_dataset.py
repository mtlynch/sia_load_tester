import os
import shutil
import tempfile
import unittest

from sia_load_tester import dataset


class DatasetTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_from_path_empty_directory_makes_dataset_with_zero_paths(self):
        d = dataset.load_from_path(self.test_dir)

        self.assertEqual(self.test_dir, d.root_dir)
        self.assertEqual([], d.paths)

    def test_load_from_path_populated_directory_makes_populated_dataset(self):
        open(os.path.join(self.test_dir, 'a.txt'), 'w').close()
        open(os.path.join(self.test_dir, 'b.txt'), 'w').close()
        open(os.path.join(self.test_dir, 'c.txt'), 'w').close()

        d = dataset.load_from_path(self.test_dir)

        self.assertEqual(self.test_dir, d.root_dir)
        self.assertItemsEqual([
            os.path.join(self.test_dir, 'a.txt'),
            os.path.join(self.test_dir, 'b.txt'),
            os.path.join(self.test_dir, 'c.txt'),
        ], d.paths)

    def test_load_from_path_nested_directory_makes_dataset_with_relative_paths(
            self):
        open(os.path.join(self.test_dir, 'a.txt'), 'w').close()
        os.makedirs(os.path.join(self.test_dir, 'foo', 'bar'))
        open(os.path.join(self.test_dir, 'foo', 'bar', 'b.txt'), 'w').close()
        os.makedirs(os.path.join(self.test_dir, 'fit', 'bat'))
        open(os.path.join(self.test_dir, 'fit', 'bat', 'c.txt'), 'w').close()

        d = dataset.load_from_path(self.test_dir)

        self.assertEqual(self.test_dir, d.root_dir)
        self.assertItemsEqual([
            os.path.join(self.test_dir, 'a.txt'),
            os.path.join(self.test_dir, 'foo/bar/b.txt'),
            os.path.join(self.test_dir, 'fit/bat/c.txt'),
        ], d.paths)

    def test_load_from_path_nonexistent_directory_raises_exception(self):
        with self.assertRaises(dataset.InvalidPath):
            dataset.load_from_path(
                os.path.join(self.test_dir, 'dummy-subdirectory'))
