import datetime
import json
import logging
import os

import pysia

logger = logging.getLogger(__name__)


def make_snapshotter(output_dir):
    return Snapshotter(output_dir, pysia.Sia(), datetime.datetime.utcnow)


class Snapshotter(object):

    def __init__(self, output_dir, sia_api, time_fn):
        self._output_dir = output_dir
        self._sia_api = sia_api
        self._time_fn = time_fn

    def snapshot(self):
        _ensure_directory_exists(self._output_dir)
        snapshot_fns = [
            self._snapshot_renter, self._snapshot_contract,
            self._snapshot_renter_prices, self._snapshot_renter_files,
            self._snapshot_wallet
        ]
        timestamp = self._time_fn()
        for snapshot_fn in snapshot_fns:
            try:
                snapshot_fn(timestamp)
            except Exception as e:
                logger.error(
                    'Error when attempting to call snapshot function %s: %s',
                    snapshot_fn.__name__, e.message)

    def _snapshot_renter(self, timestamp):
        _snapshot_api(self._sia_api.get_renter, self._output_dir, 'renter',
                      timestamp)

    def _snapshot_contract(self, timestamp):
        _snapshot_api(self._sia_api.get_renter_contracts, self._output_dir,
                      'contracts', timestamp)

    def _snapshot_renter_prices(self, timestamp):
        _snapshot_api(self._sia_api.get_renter_prices, self._output_dir,
                      'prices', timestamp)

    def _snapshot_renter_files(self, timestamp):
        _snapshot_api(self._sia_api.get_renter_files, self._output_dir, 'files',
                      timestamp)

    def _snapshot_wallet(self, timestamp):
        _snapshot_api(self._sia_api.get_wallet, self._output_dir, 'wallet',
                      timestamp)


def _ensure_directory_exists(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def _snapshot_api(sia_api_fn, output_dir, snapshot_name, timestamp):
    output_path = _make_output_path(output_dir, snapshot_name, timestamp)
    logger.info('Snapshotting %s state to %s', snapshot_name, output_path)
    with open(output_path, 'w') as output_file:
        json.dump(
            sia_api_fn(),
            output_file,
            indent=4,
            separators=(',', ': '),
            sort_keys=True)


def _make_output_path(output_dir, snapshot_name, timestamp):
    return os.path.join(output_dir, '%s-%s.json' %
                        (timestamp.strftime('%Y-%m-%dT%H%M%SZ'), snapshot_name))
