import os


def from_dataset(input_dataset):
    """Converts a Dataset to a list of Job instances.

    Args:
        input_dataset: The Dataset of files to upload to Sia.

    Returns:
        A list of upload jobs.
    """
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
