import unittest

import mock
import requests

from sia_load_tester import sia_client


class SiaClientTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_api_impl = mock.Mock()
        self.mock_sleep_fn = mock.Mock()
        self.sia_client = sia_client.SiaClient(self.mock_sia_api_impl,
                                               self.mock_sleep_fn)

    def test_renter_files_returns_all_files(self):
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
        self.assertItemsEqual([
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
        ], self.sia_client.renter_files())

    def test_renter_files_returns_empty_list_when_sia_has_no_files(self):
        self.mock_sia_api_impl.get_renter_files.return_value = {
            u'files': [],
        }
        self.assertEqual(0, len(self.sia_client.renter_files()))

    def test_renter_files_raises_SiaServerNotAvailable_after_five_failed_attempts(
            self):
        self.mock_sia_api_impl.get_renter_files.side_effect = (
            requests.exceptions.ConnectionError)

        with self.assertRaises(sia_client.SiaServerNotAvailable):
            self.sia_client.renter_files()

        self.mock_sleep_fn.assert_has_calls([
            mock.call(1),
            mock.call(5),
            mock.call(25),
            mock.call(125),
            mock.call(625)
        ])

    def test_renter_files_returns_value_if_success_after_four_failures(self):
        self.mock_sia_api_impl.get_renter_files.side_effect = [
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectionError,
            {
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
                ]
            },
        ]

        self.assertItemsEqual([
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
        ], self.sia_client.renter_files())

        self.mock_sleep_fn.assert_has_calls([
            mock.call(1),
            mock.call(5),
            mock.call(25),
            mock.call(125),
        ])

    def test_upload_file_async_calls_api_impl(self):
        self.mock_sia_api_impl.set_renter_upload.return_value = True

        self.assertTrue(
            self.sia_client.upload_file_async('foo/bar.txt', 'bar.txt'))

        self.mock_sia_api_impl.set_renter_upload.assert_called_with(
            'bar.txt', source='foo/bar.txt')
