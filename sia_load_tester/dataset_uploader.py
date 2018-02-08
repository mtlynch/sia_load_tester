import logging
import os
import time

import pysia

_MAX_CONCURRENT_UPLOADS = 5
_SLEEP_SECONDS = 15

logger = logging.getLogger(__name__)


def make_dataset_uploader(input_dataset):
    """Factory method for creating an Uploader using production settings."""
    return DatasetUploader(input_dataset, pysia.Sia(), time.sleep)


class DatasetUploader(object):
    """Uploads a full dataset of files to Sia."""

    def __init__(self, input_dataset, sia, sleep_fn):
        """Creates a new DatasetUploader instance.

        Args:
            input_dataset: The Dataset of files to upload to Sia.
            sia: An implementation of the Sia client API.
            sleep_fn: A callback function for putting the thread to sleep for
                a given number of seconds."""
        self._dataset_root = input_dataset.root_dir
        self._upload_queue = _UploadQueue(input_dataset, sia)
        self._sia = sia
        self._sleep_fn = sleep_fn

    def start(self):
        """Starts the upload process

        Begins the upload process and does not return until all files in the
        dataset are fully uploaded to Sia.
        """
        while not self._upload_queue.empty():
            if self._too_many_uploads_in_progress():
                logger.info('Too many uploads in progress: %d >= %d',
                            self._count_uploads_in_progress(),
                            _MAX_CONCURRENT_UPLOADS)
                self._wait()
            next_file_path = self._upload_queue.get()
            logger.info('Uploading next file to Sia: %s', next_file_path)
            self._upload_file_to_sia_async(next_file_path)

    def _too_many_uploads_in_progress(self):
        return self._count_uploads_in_progress() >= _MAX_CONCURRENT_UPLOADS

    def _count_uploads_in_progress(self):
        n = 0
        for sia_file in _get_renter_files(self._sia):
            if sia_file[u'uploadprogress'] < 100:
                n += 1
        return n

    def _wait(self):
        logger.info('Nothing to do. Sleeping for %d seconds', _SLEEP_SECONDS)
        self._sleep_fn(_SLEEP_SECONDS)

    def _upload_file_to_sia_async(self, local_path):
        """Starts a single file upload to Sia.

        Args:
            local_path: Path to local file to upload to Sia.
        """
        sia_path = os.path.relpath(local_path, self._dataset_root)
        return self._sia.set_renter_upload(sia_path, source=local_path)


class _UploadQueue(object):

    def __init__(self, input_dataset, sia):
        """Creates a new _UploadQueue instance.

        Creates a new queue of files to upload by starting with the full input
        dataset and removing any files that are uploaded (partially or fully) to
        Sia.

        Args:
            input_dataset: The Dataset of files to upload to Sia.
            sia: An implementation of the Sia client API.
        """
        self._file_queue = _generate_file_queue(input_dataset, sia)

    def get(self):
        return self._file_queue.pop()

    def empty(self):
        return len(self._file_queue) == 0


def _generate_file_queue(input_dataset, sia):
    local_paths = [
        os.path.join(input_dataset.root_dir, f) for f in input_dataset.filenames
    ]
    sia_paths = [f[u'localpath'] for f in _get_renter_files(sia)]
    return list(set(local_paths) - set(sia_paths))


def _get_renter_files(sia_api):
    """Retrieves the list of files known to Sia."""
    return sia_api.get_renter_files()[u'files']
