import os
import unittest

import mock

from sia_load_tester import jobs
from sia_load_tester import sia_client as sc
from sia_load_tester import upload_queue


class GenerateUploadQueueTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_api_impl = mock.Mock()
        self.mock_sia_client = sc.SiaClient(
            self.mock_sia_api_impl, sleep_fn=mock.Mock())
        # Save original path separator so that we can restore it after tests
        # modify it.
        self.original_path_sep = os.path.sep

    def tearDown(self):
        os.path.sep = self.original_path_sep

    def test_generates_empty_queue_when_all_files_already_on_sia(self):
        upload_jobs = [
            jobs.Job(local_path='/dummy-path/a.txt', sia_path='a.txt'),
            jobs.Job(local_path='/dummy-path/foo/b.txt', sia_path='foo/b.txt'),
            jobs.Job(
                local_path='/dummy-path/fiz/baz/c.txt',
                sia_path='fiz/baz/c.txt')
        ]
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
                    u'siapath': u'foo/b.txt',
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
                    u'siapath': u'fiz/baz/c.txt',
                    u'localpath': u'/dummy-path/fiz/baz/c.txt',
                    u'uploadprogress': 100,
                    u'renewing': True,
                    u'filesize': 213121263,
                    u'uploadedbytes': 1010827264,
                    u'expiration': 149134
                },
            ]
        }

        queue = upload_queue.from_upload_jobs_and_sia_client(
            upload_jobs, self.mock_sia_client)

        self.assertEqual(0, queue.qsize())

    def test_generates_upload_queue_when_no_files_are_on_sia(self):
        upload_jobs = [
            jobs.Job(local_path='/dummy-root/a.txt', sia_path='a.txt'),
            jobs.Job(
                local_path='/dummy-root/fiz/baz/c.txt',
                sia_path='fiz/baz/c.txt'),
            jobs.Job(local_path='/dummy-root/foo/b.txt', sia_path='foo/b.txt'),
        ]
        self.mock_sia_api_impl.get_renter_files.return_value = {u'files': []}

        queue = upload_queue.from_upload_jobs_and_sia_client(
            upload_jobs, self.mock_sia_client)

        self.assertEqual(
            jobs.Job(local_path='/dummy-root/a.txt', sia_path='a.txt'),
            queue.get())
        self.assertEqual(
            jobs.Job(
                local_path='/dummy-root/fiz/baz/c.txt',
                sia_path='fiz/baz/c.txt'), queue.get())
        self.assertEqual(
            jobs.Job(local_path='/dummy-root/foo/b.txt', sia_path='foo/b.txt'),
            queue.get())
