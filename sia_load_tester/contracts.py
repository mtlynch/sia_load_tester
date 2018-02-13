import logging
import time

import sia_client as sc

logger = logging.getLogger(__name__)

# Minimum number of contracts needed for contract formation to be considered
# complete.
_MIN_CONTRACTS = 50
# Wait time (in seconds) between checks for contract counts.
_WAIT_SECONDS_FOR_CONTRACT_CHECKS = 30


class Error(Exception):
    pass


class ZeroBalanceError(Error):
    pass


class BuyAllowanceError(Error):
    pass


def ensure_min_contracts():
    initiator = Initiator(
        Buyer(sc.make_sia_client()), Waiter(sc.make_sia_client(), time.sleep))
    initiator.ensure_sia_has_enough_contracts()


class Initiator(object):
    """Initiates storage contracts if contracts are needed."""

    def __init__(self, buyer, waiter):
        self.buyer = buyer
        self.waiter = waiter

    def ensure_sia_has_enough_contracts(self):
        """Ensures that Sia node has enough storage contracts

        Checks if the Sia node has a storage contract budget and waits until
        Sia forms the min number of storage contracts.
        """
        self.buyer.buy_contracts_if_needed()
        self.waiter.wait_until_min_contracts_formed()


class Buyer(object):
    """Purchases storage contracts if Sia node does not already have them."""

    def __init__(self, sia_client):
        self._sia_client = sia_client

    def buy_contracts_if_needed(self):
        if not self._is_allowance_budget_set():
            logger.info('No allowance budget set')
            self._set_allowance_budget_to_wallet_balance()

    def _is_allowance_budget_set(self):
        return self._sia_client.allowance_budget() > 0

    def _set_allowance_budget_to_wallet_balance(self):
        balance = self._sia_client.wallet_balance()
        logger.info('Wallet balance is %.1f SC', _hastings_to_siacoins(balance))
        if balance <= 0:
            raise ZeroBalanceError(
                'Not enough balance to form renter contracts')
        logger.info('Setting contract budget to %.1f SC',
                    _hastings_to_siacoins(balance))
        response = self._sia_client.set_allowance_budget(balance)
        if response != True:
            error_message = 'Failed to set allowance budget to %d' % balance
            if response.has_key(u'message'):
                error_message += ': %s' % response[u'message']
            raise BuyAllowanceError(error_message)


class Waiter(object):
    """Blocks thread until Sia has the min number of contracts required."""

    def __init__(self, sia_client, sleep_fn):
        self._sia_client = sia_client
        self._sleep_fn = sleep_fn

    def wait_until_min_contracts_formed(self):
        contract_count = self._sia_client.contract_count()
        while contract_count < _MIN_CONTRACTS:
            logger.info(
                'Waiting for contract formation. %d/%d contracts formed.',
                contract_count, _MIN_CONTRACTS)
            self._sleep_fn(_WAIT_SECONDS_FOR_CONTRACT_CHECKS)
            contract_count = self._sia_client.contract_count()
        logger.info('Minimum storage contracts met: %d contracts found',
                    contract_count)


def _hastings_to_siacoins(hastings):
    return hastings * pow(10, -24)
