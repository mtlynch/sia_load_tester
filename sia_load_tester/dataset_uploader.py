import logging
import time

import sia_client as sc

_MAX_CONCURRENT_UPLOADS = 5
_SLEEP_SECONDS = 15

logger = logging.getLogger(__name__)


def make_dataset_uploader(upload_queue):
    """Factory for creating a DatasetUploader using production settings."""
    return DatasetUploader(upload_queue, sc.make_sia_client(), time.sleep)


class DatasetUploader(object):
    """Uploads a full dataset of files to Sia."""

    def __init__(self, upload_queue, sia_client, sleep_fn):
        """Creates a new DatasetUploader instance.

        Args:
            upload_queue: The queue of upload jobs.
            sia_client: An implementation of the Sia client API.
            sleep_fn: A callback function for putting the thread to sleep for
                a given number of seconds.
        """
        self._upload_queue = upload_queue
        self._sia_client = sia_client
        self._sleep_fn = sleep_fn

    def upload(self):
        """Uploads the dataset to Sia.

        Uploads and does not return until all files in the dataset are fully
        uploaded to Sia.
        """
        while not self._upload_queue.empty():
            logger.info('%d files left to upload', self._upload_queue.qsize())
            self._wait_until_next_upload()
            job = self._upload_queue.get()
            if not self._process_upload_job_async(job):
                self._upload_queue.put(job)
        self._wait_until_zero_uploads_in_progress()

    def _wait_until_next_upload(self):
        while self._too_many_uploads_in_progress():
            logger.info(('Too many uploads in progress: %d >= %d.'
                         ' Sleeping for %d seconds'),
                        self._count_uploads_in_progress(),
                        _MAX_CONCURRENT_UPLOADS, _SLEEP_SECONDS)
            self._sleep_fn(_SLEEP_SECONDS)

    def _too_many_uploads_in_progress(self):
        return self._count_uploads_in_progress() >= _MAX_CONCURRENT_UPLOADS

    def _count_uploads_in_progress(self):
        n = 0
        for sia_file in self._sia_client.renter_files():
            if sia_file[u'uploadprogress'] < 100:
                n += 1
        return n

    def _wait_until_zero_uploads_in_progress(self):
        while self._count_uploads_in_progress() > 0:
            logger.info(
                ('Waiting for remaining uploads to complete.'
                 ' %d uploads still in progress. Sleeping for %d seconds'),
                self._count_uploads_in_progress(), _SLEEP_SECONDS)
            self._sleep_fn(_SLEEP_SECONDS)

    def _process_upload_job_async(self, job):
        """Starts a single file upload to Sia.

        Args:
            job: Sia upload job to process.
        """
        logger.info('Uploading file to Sia: %s', job.local_path)
        return self._sia_client.upload_file_async(job.local_path, job.sia_path)
