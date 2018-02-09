import functools
import inspect
import logging
import time

import pysia
import requests

logger = logging.getLogger(__name__)

_MAX_REQUEST_ATTEMPTS = 5


class Error(Exception):
    pass


class SiaServerNotAvailable(Error):
    pass


def make_sia_client():
    """Creates a SiaClient instance using production settings."""
    return SiaClient(pysia.Sia(), time.sleep)


def _NetworkErrorChecking(func):
    """Decorator for wrapping function calls with an error handler

    Function decorator that wraps the function in a handler for network errors.
    Every time there's an error, it calls the calling SiaClient instance's
    _sleep_fn method to wait an increasing amount of time until the next call,
    for a maximum of _MAX_REQUEST_ATTEMPTS calls.
    """

    @functools.wraps(func)
    def wrapper(*a, **kw):
        sia_client = a[0]
        for prior_attempts in range(_MAX_REQUEST_ATTEMPTS):
            try:
                return func(*a, **kw)
            except requests.exceptions.ConnectionError as e:
                sleep_seconds = 5**prior_attempts
                logger.warning(('Request to Sia server failed: %s(%s) -> %s'
                                '  Retrying in %d seconds'), func.__name__, kw,
                               e.message, sleep_seconds)
                sia_client._sleep_fn(sleep_seconds)
                continue
        # Make one last try. If it fails, raise a custom error.
        try:
            return func(*a, **kw)
        except requests.exceptions.ConnectionError as e:
            raise SiaServerNotAvailable(
                'Could not connect to Sia server: %s' % e.message, e)

    return wrapper


def _decorate_all_methods(decorator):
    """Class decorator which adds a function decorator to a class's methods.

    Applies a function decorator to all methods in the decorated class.
    """

    def apply_decorator(cls):
        for k, f in cls.__dict__.items():
            if inspect.isfunction(f):
                setattr(cls, k, decorator(f))
        return cls

    return apply_decorator


@_decorate_all_methods(_NetworkErrorChecking)
class SiaClient(object):
    """Client interface for Sia API functions.

    This class is a thin wrapper around pysia.
    """

    def __init__(self, api_impl, sleep_fn):
        """Creates a new SiaClient instance.

        Args:
            api_impl: Implementation of pysia interface.
            sleep_fn: A callback function for putting the thread to sleep for
                a given number of seconds.
        """
        self._api_impl = api_impl
        self._sleep_fn = sleep_fn

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
