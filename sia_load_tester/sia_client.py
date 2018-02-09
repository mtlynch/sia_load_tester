import pysia


def make_sia_client():
    """Creates a SiaClient instance using production settings."""
    return SiaClient(pysia.Sia())


class SiaClient(object):
    """Client interface for Sia API functions.

    This class is a thin wrapper around pysia.
    """

    def __init__(self, api_impl):
        """Creates a new SiaClient instance.

        Args:
            api_impl: Implementation of pysia interface.
        """
        self._api_impl = api_impl

    def renter_files(self):
        """Returns a list of files known to the Sia renter."""
        return self._api_impl.get_renter_files()[u'files']

    def upload_file_async(self, local_path, sia_path):
        """Starts an asynchronous upload of a file to Sia

        Args:
            local_path: Path to file on the local filesystem (Sia node must
                share a view of this filesystem and have access to this path).
            sia_path: Name of the file within Sia.

        Returns True on success.
        """
        return self._api_impl.set_renter_upload(sia_path, source=local_path)
