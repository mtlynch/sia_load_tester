import logging
import os

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class InvalidPath(Error):
    """Exception raised when dataset path is invalid."""
    pass


class Dataset(object):
    """Represents a set of files to use for the load test.

    The test files must be located in the root of a single directory.
    """

    def __init__(self, root_dir, paths):
        """Creates a new Dataset instance.

        Args:
            root_dir: Root directory in which dataset files are located.
            paths: Paths of the files in the dataset.
        """
        self._root_dir = root_dir
        self._paths = paths

    @property
    def root_dir(self):
        return self._root_dir

    @property
    def paths(self):
        return self._paths


def load_from_path(input_path):
    """Creates a new dataset from an input path."""
    if not os.path.exists(input_path):
        raise InvalidPath(
            'Input dataset directory does not exist: %s' % input_path)
    try:
        dataset = Dataset(input_path, _find_files_recursively(input_path))
    except OSError:
        raise InvalidPath('Unable to read dataset directory: %s' % input_path)
    logger.info('Input dataset contains %d files', len(dataset.paths))
    return dataset


def _find_files_recursively(root_dir):
    paths = []
    for root, _, filenames in os.walk(root_dir):
        for filename in filenames:
            paths.append(os.path.join(root, filename))
    return paths
