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
            if self._too_many_uploads_in_progress():
                logger.info('Too many uploads in progress: %d >= %d',
                            self._count_uploads_in_progress(),
                            _MAX_CONCURRENT_UPLOADS)
                self._wait()
            job = self._upload_queue.get()
            logger.info('Uploading next file to Sia: %s', job.local_path)
            self._process_upload_job_async(job)
        # TODO(mtlynch): Wait for uploadprogress to reach 100 for all files.

    def _too_many_uploads_in_progress(self):
        return self._count_uploads_in_progress() >= _MAX_CONCURRENT_UPLOADS

    def _count_uploads_in_progress(self):
        n = 0
        for sia_file in self._sia_client.renter_files():
            if sia_file[u'uploadprogress'] < 100:
                n += 1
        return n

    def _wait(self):
        logger.info('Nothing to do. Sleeping for %d seconds', _SLEEP_SECONDS)
        self._sleep_fn(_SLEEP_SECONDS)

    def _process_upload_job_async(self, job):
        """Starts a single file upload to Sia.

        Args:
            job: Sia upload job to process.
        """
        return self._sia_client.upload_file_async(job.local_path, job.sia_path)
