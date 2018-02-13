"""Monitors upload progress to make sure Sia is still making real progress.

This offers a collection of classes meant to monitor Sia's upload progress to
ensure progress has not stalled.
"""

import collections
import datetime
import logging
import threading
import time

import sia_client as sc

logger = logging.getLogger(__name__)

# Sia must make at least 1 GiB of upload progress within the past hour window.
TIME_WINDOW_MINUTES = 60
MINIMUM_PROGRESS_THRESHOLD = pow(2, 30)

_CHECK_FREQUENCY_IN_SECONDS = 60


def start_monitor_async(exit_event):
    """Creates a Monitor instance and starts monitoring."""
    monitor = make_monitor(exit_event)
    thread = threading.Thread(target=monitor.monitor)
    thread.daemon = True
    logger.info('Starting background thread to monitor upload progress.')
    thread.start()


def make_monitor(exit_event):
    """Creates a Monitor instance using production defaults."""
    return Monitor(
        Tracker(sc.make_sia_client(), datetime.datetime.utcnow), time.sleep,
        exit_event)


class Monitor(object):
    """Monitor that tracks upload progress and fires an event when it slows."""

    def __init__(self, tracker, sleep_fn, exit_event):
        """Creates a new Monitor instance.

        Args:
            tracker: A tracker for upload progress.
            sleep_fn: A callback function for putting the thread to sleep for
                a given number of seconds.
            exit_event: If this event is set, monitoring stops. Monitor will set
                this event if progress falls below minimum.
        """
        self._tracker = tracker
        self._sleep_fn = sleep_fn
        self._exit_event = exit_event

    def monitor(self):
        """Monitors progress until exit event or progress falls below min.

        Polls Sia to track progress regularly to track upload progress. If
        upload progress falls below the minimum required threshold, sets the
        exit event. If another thread sets the exit event, monitoring will exit
        gracefully.
        """
        while not self._exit_event.is_set():
            if self._progress_is_below_minimum():
                logger.critical('Signaling for load test to end')
                self._exit_event.set()
                return
            self._sleep_fn(_CHECK_FREQUENCY_IN_SECONDS)
        logger.info('Exit event is set. Terminating progress monitoring.')

    def _progress_is_below_minimum(self):
        bytes_uploaded = self._tracker.bytes_uploaded_in_window()
        if not bytes_uploaded:
            return False

        if bytes_uploaded < MINIMUM_PROGRESS_THRESHOLD:
            logger.critical(
                'Upload progress has slowed below minimum: %d bytes in last %d minutes (minimum=%d)',
                bytes_uploaded, TIME_WINDOW_MINUTES, MINIMUM_PROGRESS_THRESHOLD)
            return True
        return False


class Tracker(object):
    """Keeps track of changes in Sia aggregate upload progress over time."""

    def __init__(self, sia_client, time_fn):
        self._sia_client = sia_client
        self._time_fn = time_fn
        # A list of history entries, with the oldest at position 0.
        self._progress_history = []

    def bytes_uploaded_in_window(self):
        """Returns number of bytes uploaded in current time window.

        Tracker maintains a trailing time window of upload progress. This
        function returns the delta of upload progress within the window. In
        other words:

            bytes_uploaded_in_window = (bytes uploaded now) - 
                                       (bytes uploaded at window start)

        Bytes uploaded data is based on Sia API information, so if files are
        deleted from Sia, progress can be negative.

        Returns:
            Number of bytes uploaded since time window start or None if tracker
            does not have enough history for a full time window.
        """
        self._record_latest()
        self._prune_history()
        bytes_uploaded = self._window_bytes()
        if self._has_complete_time_window():
            logger.info(
                '%d bytes uploaded in time window (averaging %.2f Mbps)',
                bytes_uploaded, self._get_upload_mbps_in_time_window())
            return bytes_uploaded
        else:
            logger.info('%d bytes uploaded since tracking began (averaging %.2f Mbps)',
                        bytes_uploaded, self._get_upload_mbps_in_time_window())
            return None

    def _get_upload_mbps_in_time_window(self):
        if len(self._progress_history) < 2:
            return 0
        bytes_uploaded = self._window_bytes()
        time_window_seconds = (self._window_end_timestamp() -
                               self._window_start_timestamp()).total_seconds()
        megabits_uploaded =(bytes_uploaded * 8.0) / pow(10, 6)
        return megabits_uploaded / time_window_seconds

    def _record_latest(self):
        self._progress_history.append(
            HistoryEntry(
                timestamp=self._time_fn(),
                uploaded_bytes=self._count_uploaded_bytes()))

    def _count_uploaded_bytes(self):
        uploaded_bytes = 0
        for f in self._sia_client.renter_files():
            uploaded_bytes += f[u'uploadedbytes']
        return uploaded_bytes

    def _prune_history(self):
        """Removeis all history entries before start of time window."""
        # Walk backwards until we find a record >= TIME_WINDOW_MINUTES earlier
        # than the latest record.
        for i in range(len(self._progress_history) - 1, 0, -1):
            entry = self._progress_history[i]
            if ((self._window_end_timestamp() - entry.timestamp) >=
                    datetime.timedelta(minutes=TIME_WINDOW_MINUTES)):
                # Trim all entries prior to the current entry. Make this entry
                # the oldest.
                self._progress_history = self._progress_history[i:]
                return

    def _window_bytes(self):
        return self._window_end_bytes() - self._window_start_bytes()

    def _window_start_bytes(self):
        return self._progress_history[0].uploaded_bytes

    def _window_end_bytes(self):
        return self._progress_history[-1].uploaded_bytes

    def _window_start_timestamp(self):
        return self._progress_history[0].timestamp

    def _window_end_timestamp(self):
        return self._progress_history[-1].timestamp

    def _has_complete_time_window(self):
        return (self._window_end_timestamp() - self._window_start_timestamp()
               ) >= datetime.timedelta(minutes=TIME_WINDOW_MINUTES)


HistoryEntry = collections.namedtuple('HistoryEntry',
                                      ['timestamp', 'uploaded_bytes'])
