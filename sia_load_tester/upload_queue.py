import logging
import Queue

import sia_client as sc

logger = logging.getLogger(__name__)


def from_upload_jobs(upload_jobs):
    """Creates a new upload queue from a list of upload jobs.

    Creates a new queue of files to upload by starting with the full input
    dataset and removing any files that are uploaded (partially or fully) to
    Sia.

    Args:
        upload_jobs: The unfiltered set of upload jobs.

    Returns:
        A Queue of upload jobs, filtered to remove jobs that are already
        complete (the paths already exist on Sia).
    """
    return from_upload_jobs_and_sia_client(upload_jobs, sc.make_sia_client())


def from_upload_jobs_and_sia_client(upload_jobs, sia_client):
    """Creates a new upload queue from a dataset.

    Creates a new queue of files to upload by starting with the full input
    dataset and removing any files that are uploaded (partially or fully) to
    Sia.

    Args:
        upload_jobs: The unfiltered set of upload jobs.
        sia_client: An implementation of the Sia client interface.

    Returns:
        A Queue of upload jobs, filtered to remove jobs that are already
        complete (the paths already exist on Sia).
    """
    sia_paths = _get_sia_paths(sia_client)
    # Filter jobs for files that have already been uploaded to Sia.
    upload_jobs = [j for j in upload_jobs if j.sia_path not in sia_paths]
    logger.info('%d files already uploaded to Sia, need to upload %d more',
                len(sia_paths), len(upload_jobs))
    upload_queue = Queue.Queue()
    for upload_job in upload_jobs:
        upload_queue.put(upload_job)
    return upload_queue


def _get_sia_paths(sia_client):
    return set([f[u'siapath'] for f in sia_client.renter_files()])
