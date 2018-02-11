import os
import unittest

import mock

from sia_load_tester import dataset
from sia_load_tester import sia_client as sc
from sia_load_tester import upload_queue


class GenerateUploadQueueTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_api_impl = mock.Mock()
        self.mock_sia_client = sc.SiaClient(
            self.mock_sia_api_impl, sleep_fn=mock.Mock())

    def test_generates_empty_queue_when_all_files_already_on_sia(self):
        dummy_dataset = dataset.Dataset('/dummy-path', [
            '/dummy-path/a.txt', '/dummy-path/foo/b.txt',
            '/dummy-path/fiz/baz/c.txt'
        ])
        self.mock_sia_api_impl.get_renter_files.return_value = {
            u'files': [
                {
                    u'available': True,
                    u'redundancy': 3.4,
                    u'siapath': u'a.txt',
                    u'localpath': u'/dummy-path/a.txt',
                    u'uploadprogress': 100,
                    u'renewing': True,
                    u'filesize': 204776186,
                    u'uploadedbytes': 822083584,
                    u'expiration': 149134
                },
                {
                    u'available': True,
                    u'redundancy': 3.5,
                    u'siapath': u'b.txt',
                    u'localpath': u'/dummy-path/foo/b.txt',
                    u'uploadprogress': 100,
                    u'renewing': True,
                    u'filesize': 236596539,
                    u'uploadedbytes': 1006632960,
                    u'expiration': 149134
                },
                {
                    u'available': True,
                    u'redundancy': 3.5,
                    u'siapath': u'c.txt',
                    u'localpath': u'/dummy-path/fiz/baz/c.txt',
                    u'uploadprogress': 100,
                    u'renewing': True,
                    u'filesize': 213121263,
                    u'uploadedbytes': 1010827264,
                    u'expiration': 149134
                },
            ]
        }

        queue = upload_queue.from_dataset_and_sia_client(
            dummy_dataset, self.mock_sia_client)

        self.assertEqual(0, queue.qsize())

    def test_generates_upload_queue_when_no_files_are_on_sia(self):
        input_dataset = dataset.Dataset('/dummy-root', [
            '/dummy-root/a.txt', '/dummy-root/foo/b.txt',
            '/dummy-root/fiz/baz/c.txt'
        ])
        self.mock_sia_api_impl.get_renter_files.return_value = {u'files': []}

        queue = upload_queue.from_dataset_and_sia_client(
            input_dataset, self.mock_sia_client)

        self.assertEqual(
            upload_queue.Job(local_path='/dummy-root/a.txt', sia_path='a.txt'),
            queue.get())
        self.assertEqual(
            upload_queue.Job(
                local_path='/dummy-root/foo/b.txt', sia_path='foo/b.txt'),
            queue.get())
        self.assertEqual(
            upload_queue.Job(
                local_path='/dummy-root/fiz/baz/c.txt',
                sia_path='fiz/baz/c.txt'), queue.get())

    # Patch out path functions to simulate a Windows environment.
    @mock.patch.object(os.path, 'relpath')
    @mock.patch.object(os.path, 'normpath')
    def test_converts_path_separators_on_windows(self, normpath_patch,
                                                 relpath_patch):
        normpath_patch.side_effect = lambda p: p.replace('\\', '/')
        relpath_patch.side_effect = lambda p, _: p[len('C:\\dummy-root\\'):]

        input_dataset = dataset.Dataset(r'C:\dummy-root', [
            r'C:\dummy-root\a.txt', r'C:\dummy-root\foo\b.txt',
            r'C:\dummy-root\fiz\baz\c.txt'
        ])
        self.mock_sia_api_impl.get_renter_files.return_value = {u'files': []}

        queue = upload_queue.from_dataset_and_sia_client(
            input_dataset, self.mock_sia_client)

        self.assertEqual(
            upload_queue.Job(
                local_path=r'C:\dummy-root\a.txt', sia_path='a.txt'),
            queue.get())
        self.assertEqual(
            upload_queue.Job(
                local_path=r'C:\dummy-root\foo\b.txt', sia_path='foo/b.txt'),
            queue.get())
        self.assertEqual(
            upload_queue.Job(
                local_path=r'C:\dummy-root\fiz\baz\c.txt',
                sia_path='fiz/baz/c.txt'), queue.get())


class JobTest(unittest.TestCase):

    def test_equality(self):
        a = upload_queue.Job(local_path='/foo/bar.txt', sia_path='bar.txt')
        a_copy = upload_queue.Job(local_path='/foo/bar.txt', sia_path='bar.txt')
        b = upload_queue.Job(local_path='/bar/foo.txt', sia_path='foo.txt')
        c = upload_queue.Job(local_path='/cat/bear.txt', sia_path='bear.txt')

        self.assertEqual(a, a_copy)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(b, c)
