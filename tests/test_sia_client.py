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

    def test_allowance_budget_returns_balance_when_budget_is_set(self):
        self.mock_sia_api_impl.get_renter.return_value = {
            u'financialmetrics': {
                u'downloadspending': u'0',
                u'unspent': u'302462066279572839648071822',
                u'storagespending': u'708366410084333683830174',
                u'uploadspending': u'162900643676160001431357',
                u'contractspending': u'196666666666666666666666647'
            },
            u'currentperiod': 141021,
            u'settings': {
                u'allowance': {
                    u'funds': u'500000000000000000000000000',
                    u'renewwindow': 2160,
                    u'hosts': 50,
                    u'period': 4320
                }
            }
        }
        self.assertEqual(500000000000000000000000000,
                         self.sia_client.allowance_budget())

    def test_allowance_budget_returns_zero_when_no_budget_is_zero(self):
        self.mock_sia_api_impl.get_renter.return_value = {
            u'financialmetrics': {
                u'downloadspending': u'0',
                u'unspent': u'0',
                u'storagespending': u'0',
                u'uploadspending': u'0',
                u'contractspending': u'0'
            },
            u'currentperiod': 0,
            u'settings': {
                u'allowance': {
                    u'funds': u'0',
                    u'renewwindow': 0,
                    u'hosts': 0,
                    u'period': 0
                }
            }
        }
        self.assertEqual(0, self.sia_client.allowance_budget())

    def test_is_wallet_locked_returns_true_when_wallet_is_locked(self):
        self.mock_sia_api_impl.get_wallet.return_value = {
            u'dustthreshold': u'30000000000000000000',
            u'unlocked': False,
            u'encrypted': True,
            u'confirmedsiacoinbalance': u'500000000000000000000000000',
            u'rescanning': False,
            u'unconfirmedincomingsiacoins': u'0',
            u'siacoinclaimbalance': u'0',
            u'unconfirmedoutgoingsiacoins': u'0',
            u'siafundbalance': u'0'
        }
        self.assertTrue(self.sia_client.is_wallet_locked())

    def test_is_wallet_locked_returns_false_when_wallet_is_unlocked(self):
        self.mock_sia_api_impl.get_wallet.return_value = {
            u'dustthreshold': u'30000000000000000000',
            u'unlocked': True,
            u'encrypted': True,
            u'confirmedsiacoinbalance': u'500000000000000000000000000',
            u'rescanning': False,
            u'unconfirmedincomingsiacoins': u'0',
            u'siacoinclaimbalance': u'0',
            u'unconfirmedoutgoingsiacoins': u'0',
            u'siafundbalance': u'0'
        }
        self.assertFalse(self.sia_client.is_wallet_locked())

    def test_wallet_balance_returns_balance_when_wallet_has_siacoins(self):
        self.mock_sia_api_impl.get_wallet.return_value = {
            u'dustthreshold': u'30000000000000000000',
            u'unlocked': True,
            u'encrypted': True,
            u'confirmedsiacoinbalance': u'500000000000000000000000000',
            u'rescanning': False,
            u'unconfirmedincomingsiacoins': u'0',
            u'siacoinclaimbalance': u'0',
            u'unconfirmedoutgoingsiacoins': u'0',
            u'siafundbalance': u'0'
        }
        self.assertEqual(500000000000000000000000000,
                         self.sia_client.wallet_balance())

    def test_wallet_balance_returns_zero_when_wallet_is_empty(self):
        self.mock_sia_api_impl.get_wallet.return_value = {
            u'dustthreshold': u'30000000000000000000',
            u'unlocked': True,
            u'encrypted': True,
            u'confirmedsiacoinbalance': u'0',
            u'rescanning': False,
            u'unconfirmedincomingsiacoins': u'0',
            u'siacoinclaimbalance': u'0',
            u'unconfirmedoutgoingsiacoins': u'0',
            u'siafundbalance': u'0'
        }
        self.assertEqual(0, self.sia_client.wallet_balance())

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
