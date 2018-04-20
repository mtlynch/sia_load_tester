import os

# Limit to this many copies. Mainly for formatting siapaths cleanly.
MAX_DATASET_COPIES = 100000000


class Error(Exception):
    pass


class InvalidCopyCountError(Error):
    pass


def from_dataset(input_dataset, dataset_copies):
    """Converts a Dataset to a list of Job instances.

    Args:
        input_dataset: The Dataset of files to upload to Sia.
        dataset_copies: The number of times each file in the dataset should be
            uploaded to Sia.

    Returns:
        A list of upload jobs.
    """
    jobs = []
    if dataset_copies < 1 or dataset_copies > MAX_DATASET_COPIES:
        raise InvalidCopyCountError(
            'dataset_copies must be an integer between 1 and %d. got: %d' %
            (MAX_DATASET_COPIES, dataset_copies))
    for copy_index in xrange(dataset_copies):
        for local_path in input_dataset.paths:
            sia_path = _local_path_to_sia_path(local_path,
                                               input_dataset.root_dir)
            if dataset_copies != 1:
                sia_path = _append_file_index(sia_path, copy_index)
            jobs.append(Job(local_path, sia_path))
    return jobs


def _local_path_to_sia_path(local_path, dataset_root_dir):
    sia_path = os.path.relpath(local_path, dataset_root_dir)
    path_separator = os.path.sep
    # Normalize to forward slash path separators.
    return sia_path.replace(path_separator, '/')


def _append_file_index(sia_path, copy_index):
    """Appends a file index to a Sia path to represent which copy this is.

    Args:
        sia_path: The original Sia path before the copy index is added.
        copy_index: An index of which copy number this file is.

    Returns:
        An indexed path, for example ('foo/bar.txt', 5) returns:

            foo/bar-00000005.txt
    """
    base_path, extension = os.path.splitext(sia_path)
    return '%s-%08d%s' % (base_path, copy_index, extension)


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
