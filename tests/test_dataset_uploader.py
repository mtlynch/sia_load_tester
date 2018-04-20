import threading
import unittest

import mock

from sia_load_tester import jobs
from sia_load_tester import dataset_uploader
from sia_load_tester import sia_client as sc
from sia_load_tester import upload_queue


class DatasetUploaderTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_api_impl = mock.Mock()
        mock_sleep_fn = mock.Mock()
        self.mock_sia_client = sc.SiaClient(self.mock_sia_api_impl,
                                            mock_sleep_fn)
        self.mock_condition_waiter = mock.Mock()
        self.exit_event = threading.Event()

    def test_blocks_until_all_uploads_complete(self):
        upload_jobs = [
            jobs.Job(local_path='/dummy-path/1.txt', sia_path='1.txt'),
            jobs.Job(local_path='/dummy-path/2.txt', sia_path='2.txt'),
            jobs.Job(local_path='/dummy-path/3.txt', sia_path='3.txt'),
        ]
        self.mock_sia_api_impl.get_renter_files.return_value = {
            u'files': [
                {
                    u'siapath': u'1.txt',
                    u'localpath': u'/dummy-path/1.txt',
                    u'uploadprogress': 15,
                },
                {
                    u'siapath': u'2.txt',
                    u'localpath': u'/dummy-path/2.txt',
                    u'uploadprogress': 18,
                },
                {
                    u'siapath': u'3.txt',
                    u'localpath': u'/dummy-path/3.txt',
                    u'uploadprogress': 19,
                },
            ]
        }
        queue = upload_queue.from_upload_jobs_and_sia_client(
            upload_jobs, self.mock_sia_client)
        uploader = dataset_uploader.DatasetUploader(queue, self.mock_sia_client,
                                                    self.mock_condition_waiter,
                                                    self.exit_event)

        uploader.upload()

        self.assertFalse(self.mock_sia_api_impl.set_renter_upload.called)
        self.assertEqual(1, self.mock_condition_waiter.
                         wait_for_all_uploads_to_complete.call_count)
        self.assertTrue(self.exit_event.is_set())

    def test_does_not_start_new_uploads_when_too_many_uploads_are_in_progress(
            self):
        upload_jobs = [
            jobs.Job(local_path='/dummy-path/1.txt', sia_path='1.txt'),
            jobs.Job(local_path='/dummy-path/2.txt', sia_path='2.txt'),
            jobs.Job(local_path='/dummy-path/3.txt', sia_path='3.txt'),
            jobs.Job(local_path='/dummy-path/4.txt', sia_path='4.txt'),
            jobs.Job(local_path='/dummy-path/5.txt', sia_path='5.txt'),
            jobs.Job(local_path='/dummy-path/6.txt', sia_path='6.txt'),
            jobs.Job(local_path='/dummy-path/7.txt', sia_path='7.txt'),
        ]
        self.mock_sia_api_impl.get_renter_files.return_value = {
            u'files': [
                {
                    u'siapath': u'1.txt',
                    u'localpath': u'/dummy-path/1.txt',
                    u'uploadprogress': 15,
                },
                {
                    u'siapath': u'2.txt',
                    u'localpath': u'/dummy-path/2.txt',
                    u'uploadprogress': 18,
                },
                {
                    u'siapath': u'3.txt',
                    u'localpath': u'/dummy-path/3.txt',
                    u'uploadprogress': 19,
                },
                {
                    u'siapath': u'4.txt',
                    u'localpath': u'/dummy-path/4.txt',
                    u'uploadprogress': 16,
                },
                {
                    u'siapath': u'5.txt',
                    u'localpath': u'/dummy-path/5.txt',
                    u'uploadprogress': 5,
                },
            ]
        }
        self.mock_sia_api_impl.set_renter_upload.return_value = True
        queue = upload_queue.from_upload_jobs_and_sia_client(
            upload_jobs, self.mock_sia_client)
        uploader = dataset_uploader.DatasetUploader(queue, self.mock_sia_client,
                                                    self.mock_condition_waiter,
                                                    self.exit_event)

        uploader.upload()

        self.mock_sia_api_impl.set_renter_upload.assert_has_calls([
            mock.call('6.txt', source='/dummy-path/6.txt'),
            mock.call('7.txt', source='/dummy-path/7.txt')
        ])
        self.assertEqual(
            2,
            self.mock_condition_waiter.wait_for_available_upload_slot.call_count
        )
        self.assertEqual(1, self.mock_condition_waiter.
                         wait_for_all_uploads_to_complete.call_count)
        self.assertTrue(self.exit_event.is_set())

    def test_swallows_exceptions_instead_of_interrupting_upload(self):
        upload_jobs = [
            jobs.Job(local_path='/dummy-path/a.txt', sia_path='a.txt'),
            jobs.Job(local_path='/dummy-path/b.txt', sia_path='b.txt'),
        ]
        self.mock_sia_api_impl.get_renter_files.return_value = {u'files': None}
        self.mock_sia_api_impl.set_renter_upload.side_effect = [
            ValueError('dummy upload error'), True
        ]
        queue = upload_queue.from_upload_jobs_and_sia_client(
            upload_jobs, self.mock_sia_client)
        uploader = dataset_uploader.DatasetUploader(queue, self.mock_sia_client,
                                                    self.mock_condition_waiter,
                                                    self.exit_event)

        uploader.upload()

        self.mock_sia_api_impl.set_renter_upload.assert_has_calls([
            mock.call('a.txt', source='/dummy-path/a.txt'),
            mock.call('b.txt', source='/dummy-path/b.txt'),
            mock.call('a.txt', source='/dummy-path/a.txt'),
            mock.call('a.txt', source='/dummy-path/a.txt'),
        ])
        self.assertEqual(1, self.mock_condition_waiter.
                         wait_for_all_uploads_to_complete.call_count)
        self.assertTrue(self.exit_event.is_set())
