import os


class Error(Exception):
    pass


class InvalidPath(Error):
    """Exception raised when dataset path is invalid."""
    pass


class Dataset(object):
    """Represents a set of files to use for the load test.

    The test files must be located in the root of a single directory.
    """

    def __init__(self, root_dir, filenames):
        """Creates a new Dataset instance.

        Args:
            root_dir: Root directory in which dataset files are located.
            filenames: Basenames of the files in the dataset.
        """
        self._root_dir = root_dir
        self._filenames = filenames

    @property
    def root_dir(self):
        return self._root_dir

    @property
    def filenames(self):
        return self._filenames


def load_from_path(input_path):
    """Creates a new dataset from an input path."""
    try:
        return Dataset(input_path, os.listdir(input_path))
    except OSError:
        raise InvalidPath('Unable to read dataset directory: %s' % input_path)
