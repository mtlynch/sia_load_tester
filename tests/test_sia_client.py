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

    def test_is_blockchain_synced_returns_true_when_synced(self):
        self.mock_sia_api_impl.get_consensus.return_value = {
            u'synced':
            True,
            u'difficulty':
            u'6351181658999191728',
            u'currentblock':
            u'0000000000000002b9ae8cd6e389339418eb4c2b0cf97088803e60c0ecd6487a',
            u'target': [
                0, 0, 0, 0, 0, 0, 0, 2, 231, 138, 152, 253, 47, 201, 20, 114,
                169, 34, 117, 52, 54, 52, 126, 43, 247, 116, 182, 49, 105, 90,
                108, 48
            ],
            u'height':
            141190
        }
        self.assertTrue(self.sia_client.is_blockchain_synced())

    def test_is_blockchain_synced_returns_false_when_not_synced(self):
        self.mock_sia_api_impl.get_consensus.return_value = {
            u'synced': False,
            u'height': 141189
        }
        self.assertFalse(self.sia_client.is_blockchain_synced())

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

    def test_set_allowance_budget_sets_allowance_budget(self):
        self.mock_sia_api_impl.set_renter.return_value = True

        self.assertTrue(
            self.sia_client.set_allowance_budget(500000000000000000000000000))

        self.mock_sia_api_impl.set_renter.assert_called_with(
            500000000000000000000000000, period=12960)

    def test_set_allowance_budget_returns_false_on_error(self):
        self.mock_sia_api_impl.set_renter.return_value = {
            u'message': 'dummy error message'
        }

        self.assertFalse(
            self.sia_client.set_allowance_budget(500000000000000000000000000))

    def test_contract_count_is_zero_when_no_contracts_exist(self):
        self.mock_sia_api_impl.get_renter_contracts.return_value = {
            u'contracts': []
        }
        self.assertEqual(0, self.sia_client.contract_count())

    def test_contract_count_matches_number_of_contracts(self):
        self.mock_sia_api_impl.get_renter_contracts.return_value = {
            u'contracts': [
                {
                    u'downloadspending':
                    u'0',
                    u'totalcost':
                    u'3333333333333333333333333',
                    u'lasttransaction': {
                        u'minerfees': [],
                        u'siacoininputs': [],
                        u'filecontracts': [],
                        u'storageproofs': [],
                        u'filecontractrevisions': [{
                            u'newwindowstart':
                            145341,
                            u'newfilemerkleroot':
                            u'f0880c11f4877fbf1baaf464c6543330fe47e7745dbfc872d4cfbfab1a4b533e',
                            u'newwindowend':
                            145485,
                            u'newunlockhash':
                            u'1fa5f25ccfede9cc323410d88c5dbcd0f1f6794174f2532193b33656374765e856534ca2feca',
                            u'newvalidproofoutputs': [{
                                u'unlockhash':
                                u'69a3f1fb7482ce191caefa164b0599c198cb4816c3943681568883ecc8461b8a3a4273c355c6',
                                u'value':
                                u'764906402646858466136008'
                            }, {
                                u'unlockhash':
                                u'4ff1aacbc06e80e7f47ec779500d0b03ee5b425a9965e3919156314af3ff8a67c9032a983c68',
                                u'value':
                                u'21393865794386173135848413'
                            }],
                            u'newrevisionnumber':
                            407,
                            u'parentid':
                            u'2f0b407959b78e4f2e68dc21e3857be2e79f4ec81a1f935b84994c369fbe9709',
                            u'newfilesize':
                            1702887424,
                            u'unlockconditions': {
                                u'signaturesrequired':
                                2,
                                u'publickeys': [{
                                    u'key':
                                    u'It2tcsayHZ7aFlWuTEYhtDqIUcLKOJOVIWbWC66nIBQ=',
                                    u'algorithm':
                                    u'ed25519'
                                }, {
                                    u'key':
                                    u'SDveQv70LLqGLH9qX7H2ilsp/x6+hUwvOe0H0H7fMZo=',
                                    u'algorithm':
                                    u'ed25519'
                                }],
                                u'timelock':
                                0
                            },
                            u'newmissedproofoutputs': [{
                                u'unlockhash':
                                u'69a3f1bf7482ce191caefa146b0599c198cb4816c3943681568883ecc8461b8a3a4273c355c6',
                                u'value':
                                u'764906420646858466136008'
                            }, {
                                u'unlockhash':
                                u'4ff1aacb0c6e80e7f47ec779050d0b03ee5b425a9965e3919156314af3ff8a67c9032a983c68',
                                u'value':
                                u'20125874990710670636204846'
                            }, {
                                u'unlockhash':
                                u'000000000000000000000000000000000000000000000000000000000000000089eb0d6aa869',
                                u'value':
                                u'1267990758675502499643567'
                            }]
                        }],
                        u'siacoinoutputs': [],
                        u'arbitrarydata': [],
                        u'transactionsignatures': [{
                            u'coveredfields': {
                                u'minerfees': [],
                                u'siacoininputs': [],
                                u'filecontracts': [],
                                u'storageproofs': [],
                                u'filecontractrevisions': [0],
                                u'siacoinoutputs': [],
                                u'arbitrarydata': [],
                                u'transactionsignatures': [],
                                u'wholetransaction': False,
                                u'siafundoutputs': [],
                                u'siafundinputs': []
                            },
                            u'publickeyindex':
                            0,
                            u'signature':
                            u'53o+FmQV3u3duxNN7UUUBJJ4dcZGZpv2u5ANZMCPXyQUgumuV8Z61EzRXJn0zgOfE31ZGYZW6PtL+tzVwDkwCw==',
                            u'timelock':
                            0,
                            u'parentid':
                            u'2f0b407959b78ef42e68dc21e3857be2e79f4ec81a1f935b84994c396fbe7909'
                        }, {
                            u'coveredfields': {
                                u'minerfees': [],
                                u'siacoininputs': [],
                                u'filecontracts': [],
                                u'storageproofs': [],
                                u'filecontractrevisions': [0],
                                u'siacoinoutputs': [],
                                u'arbitrarydata': [],
                                u'transactionsignatures': [],
                                u'wholetransaction': False,
                                u'siafundoutputs': [],
                                u'siafundinputs': []
                            },
                            u'publickeyindex':
                            1,
                            u'signature':
                            u'Sxu90KjYwxlacMn3ygYHhwSEgTqakFa2pO3/CiiVfRg6PUuT1kfJdGiconFHL0iAJtoou10idLaCpkc9K+yVDQ==',
                            u'timelock':
                            0,
                            u'parentid':
                            u'2f0b407959b78ef42e68dc21e3857be2e79f4ec81a1f935b84994c396feb9709'
                        }],
                        u'siafundoutputs': [],
                        u'siafundinputs': []
                    },
                    u'netaddress':
                    u'85.225.17.9:9982',
                    u'hostpublickey': {
                        u'key': u'SDveQv70LLqGL9HqX72Hilsp/x6+hUwvOe0H0H7fMZo=',
                        u'algorithm': u'ed25519'
                    },
                    u'uploadspending':
                    u'1719916298240000015022',
                    u'endheight':
                    145341,
                    u'renterfunds':
                    u'764906420646858466136008',
                    u'fees':
                    u'2460703386713099097270000',
                    u'StorageSpending':
                    u'106003609675135769912303',
                    u'id':
                    u'2f0b407959b78ef42e68d2c1e3857be2e7f94ec81a1f935b84994c369fbe9709',
                    u'startheight':
                    141023,
                    u'size':
                    1702887424
                },
                {
                    u'downloadspending':
                    u'0',
                    u'totalcost':
                    u'3333333333333333333333333',
                    u'lasttransaction': {
                        u'minerfees': [],
                        u'siacoininputs': [],
                        u'filecontracts': [],
                        u'storageproofs': [],
                        u'filecontractrevisions': [{
                            u'newwindowstart':
                            145341,
                            u'newfilemerkleroot':
                            u'c1f2c256945b1c462e18f18ba81cfa88adbcefa21c195afbda14d9f9c7ad0ec3',
                            u'newwindowend':
                            145485,
                            u'newunlockhash':
                            u'c5951eb8d412501f3dc942e2cf30a36f092ebd3a86d6b494f570ca10f7917da2656137a17c2a',
                            u'newvalidproofoutputs': [{
                                u'unlockhash':
                                u'da77b9b7a98884ec5bb4d038e1983036b453c4d93d07df38f68dd0816f7f1b96e203b32e3e0e',
                                u'value':
                                u'1348292646146179933196409'
                            }, {
                                u'unlockhash':
                                u'68a791de6cc5da676b79935bb517999c596d9a42778298716317bf1f322415dbf72ac1343421',
                                u'value':
                                u'19262312793853796385492476'
                            }],
                            u'newrevisionnumber':
                            407,
                            u'parentid':
                            u'41e46b850b493163e5138472ec3c79fb4e219f0733ef69f6ca9b72fc07355f71',
                            u'newfilesize':
                            1702887424,
                            u'unlockconditions': {
                                u'signaturesrequired':
                                2,
                                u'publickeys': [{
                                    u'key':
                                    u'Rm2FElL6/i3rfLlUIgYqoHKGfk7QjU7khzTZk2ZcFX8=',
                                    u'algorithm':
                                    u'ed25519'
                                }, {
                                    u'key':
                                    u'q7RrAffT9tt2fufB4785p7T6Mvq2sbgRAlRhmchKoS0=',
                                    u'algorithm':
                                    u'ed25519'
                                }],
                                u'timelock':
                                0
                            },
                            u'newmissedproofoutputs': [{
                                u'unlockhash':
                                u'da77b9b7a98884ec5bb4d038e1938036b453c4d93d07df38f68dd0816f7f1b96e203b32e3e0e',
                                u'value':
                                u'1348292646146179933196409'
                            }, {
                                u'unlockhash':
                                u'68a791de6cc5da676b97935bb157999c596d9a42778298716317bf1f322415dbf72ac1343421',
                                u'value':
                                u'18828797854517391993134109'
                            }, {
                                u'unlockhash':
                                u'000000000000000000000000000000000000000000000000000000000000000089eb0d6a8a69',
                                u'value':
                                u'433514939336404392358367'
                            }]
                        }],
                        u'siacoinoutputs': [],
                        u'arbitrarydata': [],
                        u'transactionsignatures': [{
                            u'coveredfields': {
                                u'minerfees': [],
                                u'siacoininputs': [],
                                u'filecontracts': [],
                                u'storageproofs': [],
                                u'filecontractrevisions': [0],
                                u'siacoinoutputs': [],
                                u'arbitrarydata': [],
                                u'transactionsignatures': [],
                                u'wholetransaction': False,
                                u'siafundoutputs': [],
                                u'siafundinputs': []
                            },
                            u'publickeyindex':
                            0,
                            u'signature':
                            u'POJlCLg1ArARgrbRVzIs0IzAVSELxsFvfF4/kclwCU+DfYgbM4PcGLMSHjWdnuQ7uH2h8SLde29lR8ayHyWXBQ==',
                            u'timelock':
                            0,
                            u'parentid':
                            u'41e46b850b493163e5138472ec3c79bf42e19f0733ef69f6ca9b72fc07355f71'
                        }, {
                            u'coveredfields': {
                                u'minerfees': [],
                                u'siacoininputs': [],
                                u'filecontracts': [],
                                u'storageproofs': [],
                                u'filecontractrevisions': [0],
                                u'siacoinoutputs': [],
                                u'arbitrarydata': [],
                                u'transactionsignatures': [],
                                u'wholetransaction': False,
                                u'siafundoutputs': [],
                                u'siafundinputs': []
                            },
                            u'publickeyindex':
                            1,
                            u'signature':
                            u'xGWawmN21NHj2XzYP/9RjK9nK7dvGBp6YaRiXa9Whd8CsRETax+cUJ1UgGCvUV9BzCPaTyvGJAQHsFxYTlMkAQ==',
                            u'timelock':
                            0,
                            u'parentid':
                            u'41e46b850b493163e5138472ec3c79bf4e129f0733ef69f6ca9b72fc07355f71'
                        }],
                        u'siafundoutputs': [],
                        u'siafundinputs': []
                    },
                    u'netaddress':
                    u'padron.asuscomm.com:9982',
                    u'hostpublickey': {
                        u'key': u'q7RrAffT9tt2fufB4785p7T6Mvq2sbgRAlRhmchKoS0=',
                        u'algorithm': u'ed25519'
                    },
                    u'uploadspending':
                    u'42997907456000000377986',
                    u'endheight':
                    145341,
                    u'renterfunds':
                    u'1348292646146179933196409',
                    u'fees':
                    u'1897874559999999038940000',
                    u'StorageSpending':
                    u'44168219731154360818938',
                    u'id':
                    u'41e46b850b493163e5138472ec3c79bf4e219f0733e6f9f6ca9b72fc07355f71',
                    u'startheight':
                    141023,
                    u'size':
                    1702887424
                },
            ],
        }
        self.assertEqual(2, self.sia_client.contract_count())

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

    def test_upload_file_async_returns_false_on_error(self):
        self.mock_sia_api_impl.set_renter_upload.return_value = {
            u'message': u'upload failed: dummy error message.'
        }

        self.assertFalse(
            self.sia_client.upload_file_async('foo/bar.txt', 'bar.txt'))

        self.mock_sia_api_impl.set_renter_upload.assert_called_with(
            'bar.txt', source='foo/bar.txt')
