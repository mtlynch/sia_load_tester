import unittest

import mock

from sia_load_tester import contracts


class InitiatorTest(unittest.TestCase):

    def setUp(self):
        pass


class BuyerTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_client = mock.Mock()
        self.buyer = contracts.Buyer(self.mock_sia_client)

    def test_does_not_buy_if_allowance_is_already_set(self):
        self.mock_sia_client.allowance_budget.return_value = 2
        self.mock_sia_client.wallet_balance.return_value = 5

        self.buyer.buy_contracts_if_needed()

        self.assertFalse(self.mock_sia_client.set_allowance_budget.called)

    def test_buys_contracts_when_no_allowance_is_set(self):
        self.mock_sia_client.allowance_budget.return_value = 0
        self.mock_sia_client.wallet_balance.return_value = 5

        self.buyer.buy_contracts_if_needed()

        self.mock_sia_client.set_allowance_budget.assert_called_once_with(5)

    def test_raises_ZeroBalanceError_when_wallet_balance_is_zero(self):
        self.mock_sia_client.allowance_budget.return_value = 0
        self.mock_sia_client.wallet_balance.return_value = 0

        with self.assertRaises(contracts.ZeroBalanceError):
            self.buyer.buy_contracts_if_needed()


class WaiterTest(unittest.TestCase):

    def setUp(self):
        self.mock_sia_client = mock.Mock()
        self.mock_sleep_fn = mock.Mock()
        self.waiter = contracts.Waiter(self.mock_sia_client, self.mock_sleep_fn)

    def test_does_not_wait_when_min_contracts_already_formed(self):
        self.mock_sia_client.contract_count.return_value = 50

        self.waiter.wait_until_min_contracts_formed()

        self.assertFalse(self.mock_sleep_fn.called)

    def test_sleeps_until_min_contracts_are_formed(self):
        self.mock_sia_client.contract_count.side_effect = [1, 5, 25, 50]

        self.waiter.wait_until_min_contracts_formed()

        # If it takes 4 checks of contract_count() until waiter reaches the min
        # number of contracts, we expect 4 - 1 = 3 sleep calls.
        self.assertEqual(3, self.mock_sleep_fn.call_count)
