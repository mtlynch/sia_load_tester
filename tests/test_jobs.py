import os
import unittest

import mock

from sia_load_tester import dataset
from sia_load_tester import jobs


class GenerateUploadJobsTest(unittest.TestCase):

    def setUp(self):
        # Save original path separator so that we can restore it after tests
        # modify it.
        self.original_path_sep = os.path.sep

    def tearDown(self):
        os.path.sep = self.original_path_sep

    def test_generates_empty_job_list_when_dataset_is_empty(self):
        input_dataset = dataset.Dataset('/dummy-path', [])
        self.assertEqual([], jobs.from_dataset(input_dataset, dataset_copies=1))

    def test_generates_correct_jobs_from_dataset(self):
        input_dataset = dataset.Dataset('/dummy-path', [
            '/dummy-path/a.txt',
            '/dummy-path/fiz/baz/c.txt',
            '/dummy-path/foo/b.txt',
        ])
        self.assertEqual([
            jobs.Job(local_path='/dummy-path/a.txt', sia_path='a.txt'),
            jobs.Job(
                local_path='/dummy-path/fiz/baz/c.txt',
                sia_path='fiz/baz/c.txt'),
            jobs.Job(local_path='/dummy-path/foo/b.txt', sia_path='foo/b.txt'),
        ], jobs.from_dataset(input_dataset, dataset_copies=1))

    def test_zero_dataset_copies_raises_exception(self):
        input_dataset = dataset.Dataset('/dummy-path', [
            '/dummy-path/a.txt',
            '/dummy-path/fiz/baz/c.txt',
        ])
        with self.assertRaises(jobs.InvalidCopyCountError):
            jobs.from_dataset(input_dataset, dataset_copies=0)

    def test_negative_dataset_copies_raises_exception(self):
        input_dataset = dataset.Dataset('/dummy-path', [
            '/dummy-path/a.txt',
            '/dummy-path/fiz/baz/c.txt',
        ])
        with self.assertRaises(jobs.InvalidCopyCountError):
            jobs.from_dataset(input_dataset, dataset_copies=-5)

    def test_too_many_dataset_copies_raises_exception(self):
        input_dataset = dataset.Dataset('/dummy-path', [
            '/dummy-path/a.txt',
            '/dummy-path/fiz/baz/c.txt',
        ])
        with self.assertRaises(jobs.InvalidCopyCountError):
            jobs.from_dataset(
                input_dataset, dataset_copies=(jobs.MAX_DATASET_COPIES + 1))

    def test_creates_jobs_for_copies(self):
        input_dataset = dataset.Dataset('/dummy-path', [
            '/dummy-path/a.txt',
            '/dummy-path/fiz/baz/c.txt',
        ])
        jobs.from_dataset(input_dataset, dataset_copies=3)
        self.assertEqual([
            jobs.Job(local_path='/dummy-path/a.txt', sia_path='a-00000000.txt'),
            jobs.Job(
                local_path='/dummy-path/fiz/baz/c.txt',
                sia_path='fiz/baz/c-00000000.txt'),
            jobs.Job(local_path='/dummy-path/a.txt', sia_path='a-00000001.txt'),
            jobs.Job(
                local_path='/dummy-path/fiz/baz/c.txt',
                sia_path='fiz/baz/c-00000001.txt'),
            jobs.Job(local_path='/dummy-path/a.txt', sia_path='a-00000002.txt'),
            jobs.Job(
                local_path='/dummy-path/fiz/baz/c.txt',
                sia_path='fiz/baz/c-00000002.txt'),
        ], jobs.from_dataset(input_dataset, dataset_copies=3))

    # Patch out relpath to simulate a Windows environment.
    @mock.patch.object(os.path, 'relpath')
    def test_converts_path_separators_on_windows(self, relpath_patch):
        os.path.sep = '\\'
        relpath_patch.side_effect = lambda p, _: p[len('C:\\dummy-root\\'):]

        input_dataset = dataset.Dataset(r'C:\dummy-root', [
            r'C:\dummy-root\a.txt',
            r'C:\dummy-root\fiz\baz\c.txt',
            r'C:\dummy-root\foo\b.txt',
        ])
        self.assertEqual([
            jobs.Job(local_path=r'C:\dummy-root\a.txt', sia_path='a.txt'),
            jobs.Job(
                local_path=r'C:\dummy-root\fiz\baz\c.txt',
                sia_path='fiz/baz/c.txt'),
            jobs.Job(
                local_path=r'C:\dummy-root\foo\b.txt', sia_path='foo/b.txt'),
        ], jobs.from_dataset(input_dataset, dataset_copies=1))


class JobTest(unittest.TestCase):

    def test_equality(self):
        a = jobs.Job(local_path='/foo/bar.txt', sia_path='bar.txt')
        a_copy = jobs.Job(local_path='/foo/bar.txt', sia_path='bar.txt')
        b = jobs.Job(local_path='/bar/foo.txt', sia_path='foo.txt')
        c = jobs.Job(local_path='/cat/bear.txt', sia_path='bear.txt')

        self.assertEqual(a, a_copy)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(b, c)

    def test_increment_failure_count(self):
        a = jobs.Job(local_path='/foo/bar.txt', sia_path='bar.txt')
        self.assertEqual(0, a.failure_count)
        a.increment_failure_count()
        self.assertEqual(1, a.failure_count)
