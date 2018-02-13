import datetime
import threading
import unittest

import mock

from sia_load_tester import progress

# Arbitrarily-chosen timeout to make sure we don't get stuck in a deadlock
# waiting for a test to complete.
WAIT_SECONDS = 0.5


class MonitorTest(unittest.TestCase):

    def setUp(self):
        self.mock_tracker = mock.Mock()
        self.mock_sleep_fn = mock.Mock()
        self.exit_event = threading.Event()
        self.monitor = progress.Monitor(self.mock_tracker, self.mock_sleep_fn,
                                        self.exit_event)
        self.monitor_thread = None

    def start_monitor_async(self):
        self.monitor_thread = threading.Thread(target=self.monitor.monitor)
        self.monitor_thread.start()

    def test_sets_exit_event_if_progress_is_below_minimum(self):
        self.mock_tracker.bytes_uploaded_in_window.side_effect = [
            None, progress.MINIMUM_PROGRESS_THRESHOLD + 5,
            progress.MINIMUM_PROGRESS_THRESHOLD,
            progress.MINIMUM_PROGRESS_THRESHOLD - 1
        ]

        self.start_monitor_async()

        self.exit_event.wait(WAIT_SECONDS)
        self.monitor_thread.join(WAIT_SECONDS)
        self.assertTrue(self.exit_event.is_set())
        # Expect a sleep call for each time the tracker reports progress above
        # minimum.
        self.assertEqual(3, self.mock_sleep_fn.call_count)

    def test_exits_when_exit_event_is_set(self):
        self.mock_tracker.bytes_uploaded_in_window.return_value = progress.MINIMUM_PROGRESS_THRESHOLD + 100

        self.start_monitor_async()
        self.exit_event.set()

        self.monitor_thread.join(WAIT_SECONDS)
        self.assertFalse(self.monitor_thread.is_alive())


class TrackerTest(unittest.TestCase):

    def setUp(self):
        self.mock_files = []
        mock_sia_client = mock.Mock()
        mock_sia_client.renter_files.side_effect = lambda: self.mock_files
        self.mock_time = datetime.datetime(1970, 1, 1, 0, 0, 0)
        mock_time_fn = lambda: self.mock_time
        self.tracker = progress.Tracker(mock_sia_client, mock_time_fn)

    def test_returns_None_when_elapsed_time_is_less_than_time_window(self):
        self.mock_files = [
            {
                u'uploadedbytes': 100,
            },
            {
                u'uploadedbytes': 200,
            },
        ]
        self.mock_time = datetime.datetime(2018, 2, 13, 0, 0, 0)
        self.assertIsNone(self.tracker.bytes_uploaded_in_window())

        self.mock_files[0][u'uploadedbytes'] = 106
        self.mock_files[1][u'uploadedbytes'] = 211

        self.mock_time += datetime.timedelta(minutes=59, seconds=59)
        self.assertIsNone(self.tracker.bytes_uploaded_in_window())

    def test_returns_byte_delta_when_elapsed_time_equals_time_window(self):
        self.mock_files = [
            {
                u'uploadedbytes': 100,
            },
            {
                u'uploadedbytes': 200,
            },
        ]
        self.mock_time = datetime.datetime(2018, 2, 13, 0, 0, 0)
        self.assertIsNone(self.tracker.bytes_uploaded_in_window())

        self.mock_files[0][u'uploadedbytes'] = 106
        self.mock_files[1][u'uploadedbytes'] = 211

        self.mock_time += datetime.timedelta(hours=1)
        self.assertEqual(17, self.tracker.bytes_uploaded_in_window())

    def test_returns_byte_delta_of_most_recent_time_window(self):
        self.mock_files = [
            {
                u'uploadedbytes': 100,
            },
            {
                u'uploadedbytes': 200,
            },
        ]
        self.mock_time = datetime.datetime(2018, 2, 13, 0, 0, 0)
        self.tracker.bytes_uploaded_in_window()

        self.mock_files[0][u'uploadedbytes'] = 106
        self.mock_files[1][u'uploadedbytes'] = 211

        self.mock_time += datetime.timedelta(hours=1)
        self.tracker.bytes_uploaded_in_window()

        self.mock_files[0][u'uploadedbytes'] = 606
        self.mock_files[1][u'uploadedbytes'] = 711

        self.mock_time += datetime.timedelta(hours=1)
        self.assertEqual(1000, self.tracker.bytes_uploaded_in_window())
