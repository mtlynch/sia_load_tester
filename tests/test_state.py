import datetime
import os
import shutil
import tempfile
import unittest

import mock

from sia_load_tester import state

_DUMMY_TIMESTAMP = datetime.datetime(2018, 2, 12, 23, 12, 51)


class SnapshotterTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.mock_sia_api = mock.Mock()
        self.test_dir = tempfile.mkdtemp()
        self.mock_time_fn = lambda: _DUMMY_TIMESTAMP
        self.snapshotter = state.Snapshotter(self.test_dir, self.mock_sia_api,
                                             self.mock_time_fn)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def assertFileContents(self, filename, contents):
        test_path = os.path.join(self.test_dir, filename)
        self.assertTrue(
            os.path.exists(test_path), 'Expected file at %s' % test_path)
        contents_actual = open(test_path).read()
        self.assertEqual(contents, contents_actual)

    def test_writes_nothing_when_all_api_calls_raise_exceptions(self):
        self.mock_sia_api.get_renter.side_effect = ValueError(
            'dummy get_renter exception')
        self.mock_sia_api.get_renter_contracts.side_effect = ValueError(
            'dummy get_renter_contracts exception')
        self.mock_sia_api.get_renter_files.side_effect = ValueError(
            'dummy get_renter_files exception')
        self.mock_sia_api.get_renter_prices.side_effect = ValueError(
            'dummy get_renter_prices exception')
        self.mock_sia_api.get_wallet.side_effect = ValueError(
            'dummy get_wallet exception')

        self.assertEqual([], os.listdir(self.test_dir))

    def test_writes_all_snapshots_state_when_all_api_calls_return_successfully(
            self):
        self.mock_sia_api.get_renter.return_value = {
            u'financialmetrics': {
                u'downloadspending': u'0',
                u'unspent': u'34797878617810340977686614',
                u'storagespending': u'49059923242626992272403653',
                u'uploadspending': u'9475531472896000083243107',
                u'contractspending': u'406666666666666666666666626'
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
        self.mock_sia_api.get_renter_contracts.return_value = {
            u'contracts': [
                {
                    u'totalcost': u'200000',
                    u'fees': u'10000',
                    u'StorageSpending': u'2000',
                    u'uploadspending': u'800',
                    u'downloadspending': u'60',
                    u'renterfunds': u'3',
                    u'size': 22,
                },
                {
                    u'totalcost': u'500000',
                    u'fees': u'70000',
                    u'StorageSpending': u'5000',
                    u'uploadspending': u'100',
                    u'downloadspending': u'10',
                    u'renterfunds': u'2',
                    u'size': 77,
                },
            ]
        }
        self.mock_sia_api.get_renter_files.return_value = {
            u'files': [
                {
                    u'filesize': 900,
                    u'uploadedbytes': 50,
                    u'uploadprogress': 90,
                },
                {
                    u'filesize': 800,
                    u'uploadedbytes': 100,
                    u'uploadprogress': 100,
                },
                {
                    u'filesize': 100,
                    u'uploadedbytes': 5,
                    u'uploadprogress': 90,
                },
            ],
        }
        self.mock_sia_api.get_renter_prices.return_value = {
            u'uploadterabyte': u'34320000000000000000000000',
            u'formcontracts': u'84350000000000000000000000',
            u'storageterabytemonth': u'126239999993769600000000000',
            u'downloadterabyte': u'21780000000000000000000000'
        }
        self.mock_sia_api.get_wallet.return_value = {
            u'dustthreshold': u'30000000000000000000',
            u'unlocked': True,
            u'encrypted': True,
            u'confirmedsiacoinbalance': u'46666666666666666666666712',
            u'rescanning': False,
            u'unconfirmedincomingsiacoins': u'0',
            u'siacoinclaimbalance': u'0',
            u'unconfirmedoutgoingsiacoins': u'0',
            u'siafundbalance': u'0'
        }

        self.snapshotter.snapshot()

        self.assertFileContents('2018-02-12T231251Z-renter.json', """
{
    "currentperiod": 141021,
    "financialmetrics": {
        "contractspending": "406666666666666666666666626",
        "downloadspending": "0",
        "storagespending": "49059923242626992272403653",
        "unspent": "34797878617810340977686614",
        "uploadspending": "9475531472896000083243107"
    },
    "settings": {
        "allowance": {
            "funds": "500000000000000000000000000",
            "hosts": 50,
            "period": 4320,
            "renewwindow": 2160
        }
    }
}
""".strip())
        self.assertFileContents('2018-02-12T231251Z-contracts.json', """
{
    "contracts": [
        {
            "StorageSpending": "2000",
            "downloadspending": "60",
            "fees": "10000",
            "renterfunds": "3",
            "size": 22,
            "totalcost": "200000",
            "uploadspending": "800"
        },
        {
            "StorageSpending": "5000",
            "downloadspending": "10",
            "fees": "70000",
            "renterfunds": "2",
            "size": 77,
            "totalcost": "500000",
            "uploadspending": "100"
        }
    ]
}
""".strip())
        self.assertFileContents('2018-02-12T231251Z-files.json', """
{
    "files": [
        {
            "filesize": 900,
            "uploadedbytes": 50,
            "uploadprogress": 90
        },
        {
            "filesize": 800,
            "uploadedbytes": 100,
            "uploadprogress": 100
        },
        {
            "filesize": 100,
            "uploadedbytes": 5,
            "uploadprogress": 90
        }
    ]
}
""".strip())
        self.assertFileContents('2018-02-12T231251Z-prices.json', """
{
    "downloadterabyte": "21780000000000000000000000",
    "formcontracts": "84350000000000000000000000",
    "storageterabytemonth": "126239999993769600000000000",
    "uploadterabyte": "34320000000000000000000000"
}
""".strip())
        self.assertFileContents('2018-02-12T231251Z-wallet.json', """
{
    "confirmedsiacoinbalance": "46666666666666666666666712",
    "dustthreshold": "30000000000000000000",
    "encrypted": true,
    "rescanning": false,
    "siacoinclaimbalance": "0",
    "siafundbalance": "0",
    "unconfirmedincomingsiacoins": "0",
    "unconfirmedoutgoingsiacoins": "0",
    "unlocked": true
}
""".strip())
