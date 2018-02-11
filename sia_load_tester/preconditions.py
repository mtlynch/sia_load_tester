"""Precondition check for Sia Load Tester

Functions for checking that Sia Load Tester's preconditions are met.
"""
import logging

import sia_client as sc

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class BlockchainNotSyncedError(Error):
    pass


class WalletLockedError(Error):
    pass


def check():
    PreconditionChecker(sc.make_sia_client()).check_preconditions()


class PreconditionChecker(object):

    def __init__(self, sia_client):
        self._sia_client = sia_client

    def check_preconditions(self):
        self._check_blockchain_sync()
        self._check_wallet_lock_status()

    def _check_blockchain_sync(self):
        logger.info('Checking that blockchain is synced')
        if not self._sia_client.is_blockchain_synced():
            raise BlockchainNotSyncedError(
                'Load tester requires a Sia node with a fully synced blockchain'
            )

    def _check_wallet_lock_status(self):
        logger.info('Checking that wallet is unlocked')
        if self._sia_client.is_wallet_locked():
            raise WalletLockedError(
                'Wallet is locked. Load tester requires an unlocked wallet.')
