import unittest

import mock

from sia_load_tester import dataset
from sia_load_tester import dataset_uploader
from sia_load_tester import sia_client as sc


class DatasetUploaderTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_api_impl = mock.Mock()
        self.mock_sia_client = sc.SiaClient(self.mock_sia_api_impl)
        self.mock_sleep_fn = mock.Mock()

    def test_exits_when_all_files_are_on_sia(self):
        dummy_dataset = dataset.Dataset('/dummy-path',
                                        ['a.txt', 'b.txt', 'c.txt'])
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
        uploader = dataset_uploader.DatasetUploader(
            dummy_dataset, self.mock_sia_client, self.mock_sleep_fn)
        uploader.start()
        self.assertEqual(0, self.mock_sia_api_impl.set_renter_upload.call_count)

    def test_uploads_file_when_one_is_missing_from_sia(self):
        dummy_dataset = dataset.Dataset('/dummy-path',
                                        ['a.txt', 'b.txt', 'c.txt'])
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
        uploader = dataset_uploader.DatasetUploader(
            dummy_dataset, self.mock_sia_client, self.mock_sleep_fn)
        uploader.start()
        self.mock_sia_api_impl.set_renter_upload.assert_called_once_with(
            'c.txt', source='/dummy-path/c.txt')
