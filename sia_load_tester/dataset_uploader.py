import logging

import sia_client as sc
import sia_conditions

_MAX_CONCURRENT_UPLOADS = 5
_SLEEP_SECONDS = 15

logger = logging.getLogger(__name__)


def make_dataset_uploader(upload_queue, exit_event):
    """Factory for creating a DatasetUploader using production settings."""
    return DatasetUploader(upload_queue, sc.make_sia_client(),
                           sia_conditions.make_waiter(exit_event), exit_event)


class DatasetUploader(object):
    """Uploads a full dataset of files to Sia."""

    def __init__(self, upload_queue, sia_client, sia_condition_waiter,
                 exit_event):
        """Creates a new DatasetUploader instance.

        Args:
            upload_queue: The queue of upload jobs.
            sia_client: An implementation of the Sia client API.
            sia_condition_waiter: An object that blocks the thread to wait for
                particular Sia conditions to be true.
            exit_event: Event to set when DatasetUploader completes upload.
        """
        self._upload_queue = upload_queue
        self._sia_client = sia_client
        self._sia_condition_waiter = sia_condition_waiter
        self._exit_event = exit_event

    def upload(self):
        """Uploads the dataset to Sia.

        Uploads and does not return until all files in the dataset are fully
        uploaded to Sia.
        """
        while not self._upload_queue.empty():
            logger.info('%d files left to upload', self._upload_queue.qsize())
            self._sia_condition_waiter.wait_for_available_upload_slot()
            job = self._upload_queue.get()
            if (not self._process_upload_job_async(job)) and (job.failure_count
                                                              < 3):
                logger.error('Adding to the queue again')
                self._upload_queue.put(job)
        self._sia_condition_waiter.wait_for_all_uploads_to_complete()
        self._exit_event.set()

    def _process_upload_job_async(self, job):
        """Starts a single file upload to Sia.

        Args:
            job: Sia upload job to process.

        Returns:
            True if upload job was sent to Sia successfully.
        """
        logger.info('Uploading file to Sia: %s', job.local_path)
        try:
            return self._sia_client.upload_file_async(job.local_path,
                                                      job.sia_path)
        except Exception as ex:
            logger.error('Upload failed: %s', ex.message)
            job.increment_failure_count()
            return False
