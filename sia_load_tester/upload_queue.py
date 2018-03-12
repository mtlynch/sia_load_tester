import logging
import os
import Queue

import sia_client as sc

logger = logging.getLogger(__name__)


def from_dataset(input_dataset):
    """Creates a new upload queue from a dataset.

    Creates a new queue of files to upload by starting with the full input
    dataset and removing any files that are uploaded (partially or fully) to
    Sia.

    Args:
        input_dataset: The Dataset of files to upload to Sia.

    Returns:
        A Queue of upload jobs.
    """
    return from_dataset_and_sia_client(input_dataset, sc.make_sia_client())


def from_dataset_and_sia_client(input_dataset, sia_client):
    """Creates a new upload queue from a dataset.

    Creates a new queue of files to upload by starting with the full input
    dataset and removing any files that are uploaded (partially or fully) to
    Sia.

    Args:
        input_dataset: The Dataset of files to upload to Sia.
        sia_client: An implementation of the Sia client interface.

    Returns:
        A Queue of upload jobs.
    """
    jobs = _dataset_to_jobs(input_dataset)
    sia_local_paths = _get_sia_local_paths(sia_client)
    # Filter jobs for files that have already been uploaded to Sia.
    jobs = [j for j in jobs if j.local_path not in sia_local_paths]
    logger.info('%d files already uploaded to Sia, need to upload %d more',
                len(sia_local_paths), len(jobs))
    upload_queue = Queue.Queue()
    for job in jobs:
        upload_queue.put(job)
    return upload_queue


def _dataset_to_jobs(input_dataset):
    """Converts a Dataset to a list of Job instances."""
    jobs = []
    for local_path in input_dataset.paths:
        sia_path = _local_path_to_sia_path(local_path, input_dataset.root_dir)
        jobs.append(Job(local_path, sia_path))
    return jobs


def _local_path_to_sia_path(local_path, dataset_root_dir):
    sia_path = os.path.relpath(local_path, dataset_root_dir)
    path_separator = os.path.sep
    # Normalize to forward slash path separators.
    return sia_path.replace(path_separator, '/')


def _get_sia_local_paths(sia_client):
    return set([f[u'localpath'] for f in sia_client.renter_files()])


class Job(object):
    """A job upload task.

    Represents the information needed to perform a single file upload from the
    local system to the Sia network.
    """

    def __init__(self, local_path, sia_path):
        self._local_path = local_path
        self._sia_path = sia_path
        self._failure_count = 0

    def __eq__(self, other):
        return ((self.local_path == other.local_path) and
                (self.sia_path == other.sia_path) and
                (self.failure_count == other.failure_count))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '%s(%s -> %s)' % (self.__class__.__name__, self._local_path,
                                 self._sia_path)

    def increment_failure_count(self):
        self._failure_count += 1

    @property
    def local_path(self):
        return self._local_path

    @property
    def sia_path(self):
        return self._sia_path

    @property
    def failure_count(self):
        return self._failure_count
