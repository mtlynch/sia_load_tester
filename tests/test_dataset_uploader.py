import unittest

import mock

from sia_load_tester import dataset
from sia_load_tester import dataset_uploader
from sia_load_tester import sia_client as sc
from sia_load_tester import upload_queue


class DatasetUploaderTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_api_impl = mock.Mock()
        self.mock_sleep_fn = mock.Mock()
        self.mock_sia_client = sc.SiaClient(self.mock_sia_api_impl,
                                            self.mock_sleep_fn)

    def test_uploads_nothing_when_all_files_are_on_sia(self):
        dummy_dataset = dataset.Dataset(
            '/dummy-path',
            ['/dummy-path/a.txt', '/dummy-path/b.txt', '/dummy-path/c.txt'])
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
                    u'localpath': u'/dummy-path/b.txt',
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
                    u'localpath': u'/dummy-path/c.txt',
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
        uploader = dataset_uploader.DatasetUploader(queue, self.mock_sia_client,
                                                    self.mock_sleep_fn)

        uploader.upload()

        self.assertFalse(self.mock_sia_api_impl.set_renter_upload.called)
        self.assertFalse(self.mock_sleep_fn.called)

    def test_uploads_file_when_one_is_missing_from_sia(self):
        dummy_dataset = dataset.Dataset(
            '/dummy-path',
            ['/dummy-path/a.txt', '/dummy-path/b.txt', '/dummy-path/c.txt'])
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
                    u'localpath': u'/dummy-path/b.txt',
                    u'uploadprogress': 100,
                    u'renewing': True,
                    u'filesize': 236596539,
                    u'uploadedbytes': 1006632960,
                    u'expiration': 149134
                },
            ]
        }
        self.mock_sia_api_impl.set_renter_upload.return_value = True
        queue = upload_queue.from_dataset_and_sia_client(
            dummy_dataset, self.mock_sia_client)
        uploader = dataset_uploader.DatasetUploader(queue, self.mock_sia_client,
                                                    self.mock_sleep_fn)

        uploader.upload()

        self.mock_sia_api_impl.set_renter_upload.assert_called_once_with(
            'c.txt', source='/dummy-path/c.txt')

    def test_blocks_until_all_uploads_complete(self):
        dummy_dataset = dataset.Dataset('/dummy-path', [
            '/dummy-path/1.txt',
            '/dummy-path/2.txt',
            '/dummy-path/3.txt',
        ])
        files_state = []
        # Initial mock file state.
        files_state.append({
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
        })
        # File state after all uploads complete.
        files_state.append({
            u'files': [
                {
                    u'siapath': u'1.txt',
                    u'localpath': u'/dummy-path/1.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'2.txt',
                    u'localpath': u'/dummy-path/2.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'3.txt',
                    u'localpath': u'/dummy-path/3.txt',
                    u'uploadprogress': 100,
                },
            ]
        })

        # Change state when sleep is called.
        def mock_sleep(sleep_seconds):
            files_state.pop(0)

        self.mock_sleep_fn.side_effect = mock_sleep

        self.mock_sia_api_impl.get_renter_files.side_effect = (
            lambda: files_state[0])

        queue = upload_queue.from_dataset_and_sia_client(
            dummy_dataset, self.mock_sia_client)
        uploader = dataset_uploader.DatasetUploader(queue, self.mock_sia_client,
                                                    self.mock_sleep_fn)

        uploader.upload()

        self.assertFalse(self.mock_sia_api_impl.set_renter_upload.called)
        self.assertEqual(1, self.mock_sleep_fn.call_count)

    def test_does_not_start_new_uploads_when_too_many_uploads_are_in_progress(
            self):
        dummy_dataset = dataset.Dataset('/dummy-path', [
            '/dummy-path/1.txt', '/dummy-path/2.txt', '/dummy-path/3.txt',
            '/dummy-path/4.txt', '/dummy-path/5.txt', '/dummy-path/6.txt',
            '/dummy-path/7.txt'
        ])
        files_state = []
        # Initial mock file state.
        files_state.append({
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
        })
        # File state after one upload completes.
        files_state.append({
            u'files': [
                {
                    u'siapath': u'1.txt',
                    u'localpath': u'/dummy-path/1.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'2.txt',
                    u'localpath': u'/dummy-path/2.txt',
                    u'uploadprogress': 88,
                },
                {
                    u'siapath': u'3.txt',
                    u'localpath': u'/dummy-path/3.txt',
                    u'uploadprogress': 79,
                },
                {
                    u'siapath': u'4.txt',
                    u'localpath': u'/dummy-path/4.txt',
                    u'uploadprogress': 56,
                },
                {
                    u'siapath': u'5.txt',
                    u'localpath': u'/dummy-path/5.txt',
                    u'uploadprogress': 95,
                },
            ]
        })
        # File state after two uploads complete.
        files_state.append({
            u'files': [
                {
                    u'siapath': u'1.txt',
                    u'localpath': u'/dummy-path/1.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'2.txt',
                    u'localpath': u'/dummy-path/2.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'3.txt',
                    u'localpath': u'/dummy-path/3.txt',
                    u'uploadprogress': 85,
                },
                {
                    u'siapath': u'4.txt',
                    u'localpath': u'/dummy-path/4.txt',
                    u'uploadprogress': 84,
                },
                {
                    u'siapath': u'5.txt',
                    u'localpath': u'/dummy-path/5.txt',
                    u'uploadprogress': 92,
                },
                {
                    u'siapath': u'6.txt',
                    u'localpath': u'/dummy-path/6.txt',
                    u'uploadprogress': 12,
                },
            ]
        })
        # File state after all uploads complete.
        files_state.append({
            u'files': [
                {
                    u'siapath': u'1.txt',
                    u'localpath': u'/dummy-path/1.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'2.txt',
                    u'localpath': u'/dummy-path/2.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'3.txt',
                    u'localpath': u'/dummy-path/3.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'4.txt',
                    u'localpath': u'/dummy-path/4.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'5.txt',
                    u'localpath': u'/dummy-path/5.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'6.txt',
                    u'localpath': u'/dummy-path/6.txt',
                    u'uploadprogress': 100,
                },
                {
                    u'siapath': u'7.txt',
                    u'localpath': u'/dummy-path/7.txt',
                    u'uploadprogress': 100,
                },
            ]
        })
        # Use a list so that mock_sleep will capture the variable. In Python 3,
        # the better solution is to use the nonlocal keyword.
        total_seconds_elapsed = [0]

        def mock_sleep(sleep_seconds):
            total_seconds_elapsed[0] += sleep_seconds

        self.mock_sleep_fn = mock_sleep

        # Simulate passage of time by returning a later state depending on how
        # many seconds the uploader has slept.
        def mock_renter_files():
            if total_seconds_elapsed[0] < 40:
                return files_state[0]
            elif total_seconds_elapsed[0] < 60:
                total_seconds_elapsed[0] += 25
                return files_state[1]
            elif total_seconds_elapsed[0] < 95:
                total_seconds_elapsed[0] += 5
                return files_state[2]
            else:
                return files_state[3]

        self.mock_sia_api_impl.get_renter_files.side_effect = mock_renter_files

        self.mock_sia_api_impl.set_renter_upload.return_value = True
        queue = upload_queue.from_dataset_and_sia_client(
            dummy_dataset, self.mock_sia_client)
        uploader = dataset_uploader.DatasetUploader(queue, self.mock_sia_client,
                                                    self.mock_sleep_fn)

        uploader.upload()

        self.mock_sia_api_impl.set_renter_upload.assert_has_calls([
            mock.call('6.txt', source='/dummy-path/6.txt'),
            mock.call('7.txt', source='/dummy-path/7.txt')
        ])
