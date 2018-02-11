import unittest

import mock

from sia_load_tester import preconditions


class PreconditionCheckerTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_client = mock.Mock()
        self.checker = preconditions.PreconditionChecker(self.mock_sia_client)

    def test_raises_WalletLockedError_if_wallet_is_locked(self):
        self.mock_sia_client.is_blockchain_synced.return_value = True
        self.mock_sia_client.is_wallet_locked.return_value = True
        with self.assertRaises(preconditions.WalletLockedError):
            self.checker.check_preconditions()

    def test_raises_BlockchainNotSyncedError_if_blockchain_is_not_synced(self):
        self.mock_sia_client.is_blockchain_synced.return_value = False
        self.mock_sia_client.is_wallet_locked.return_value = False
        with self.assertRaises(preconditions.BlockchainNotSyncedError):
            self.checker.check_preconditions()

    def test_raises_no_error_when_preconditions_are_met(self):
        self.mock_sia_client.is_blockchain_synced.return_value = True
        self.mock_sia_client.is_wallet_locked.return_value = False

        self.checker.check_preconditions()
