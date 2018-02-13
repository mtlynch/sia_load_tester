import logging
import time

import sia_client as sc

_MAX_CONCURRENT_UPLOADS = 5
_SLEEP_SECONDS = 15

logger = logging.getLogger(__name__)


def make_waiter(upload_queue):
    """Factory for creating a Waiter using production settings."""
    return Waiter(upload_queue, sc.make_sia_client(), time.sleep)


class Waiter(object):
    """Waits for conditions in Sia node to become true."""

    def __init__(self, sia_client, sleep_fn):
        """Creates a new Waiter instance.

        Args:
            sia_client: An implementation of the Sia client API.
            sleep_fn: A callback function for putting the thread to sleep for
                a given number of seconds.
        """
        self._sia_client = sia_client
        self._sleep_fn = sleep_fn

    def wait_for_available_upload_slot(self):
        upload_count = self._count_uploads_in_progress()
        while self._too_many_uploads_in_progress(upload_count):

            logger.info(('Too many uploads in progress: %d >= %d.'
                         ' Sleeping for %d seconds'), upload_count,
                        _MAX_CONCURRENT_UPLOADS, _SLEEP_SECONDS)
            self._sleep_fn(_SLEEP_SECONDS)
            upload_count = self._count_uploads_in_progress()

    def wait_for_all_uploads_to_complete(self):
        upload_count = self._count_uploads_in_progress()
        while upload_count > 0:
            logger.info(
                ('Waiting for remaining uploads to complete.'
                 ' %d uploads still in progress. Sleeping for %d seconds'),
                upload_count, _SLEEP_SECONDS)
            self._sleep_fn(_SLEEP_SECONDS)
            upload_count = self._count_uploads_in_progress()

    def _count_uploads_in_progress(self):
        n = 0
        for sia_file in self._sia_client.renter_files():
            if sia_file[u'uploadprogress'] < 100:
                n += 1
        return n

    def _too_many_uploads_in_progress(self, concurrent_uploads):
        return concurrent_uploads >= _MAX_CONCURRENT_UPLOADS
