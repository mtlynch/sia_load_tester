import unittest

import mock

from sia_load_tester import sia_conditions


class WaiterTest(unittest.TestCase):

    def setUp(self):
        self.mock_sleep_fn = mock.Mock()
        self.mock_files = []
        self.mock_sia_client = mock.Mock()
        self.mock_sia_client.renter_files.side_effect = lambda: self.mock_files
        self.waiter = sia_conditions.Waiter(self.mock_sia_client,
                                            self.mock_sleep_fn)

    def increment_upload_progress_by_one(self):
        """Simulates all files making +1% upload progress."""
        for f in self.mock_files:
            if f[u'uploadprogress'] < 100:
                f[u'uploadprogress'] += 1

    def test_wait_for_available_upload_slot_returns_immediately_when_zero_uploads_are_in_progress(
            self):
        self.mock_files = []

        self.waiter.wait_for_available_upload_slot()

        self.assertFalse(self.mock_sleep_fn.called)

    def test_wait_for_available_upload_slot_waits_until_fewer_than_five_uploads_in_progress(
            self):
        self.mock_files = [
            {
                u'uploadprogress': 90,
            },
            {
                u'uploadprogress': 91,
            },
            {
                u'uploadprogress': 92,
            },
            {
                u'uploadprogress': 93,
            },
            {
                u'uploadprogress': 94,
            },
        ]
        self.mock_sleep_fn.side_effect = lambda _: self.increment_upload_progress_by_one()

        self.waiter.wait_for_available_upload_slot()

        self.assertEqual(100 - 94, self.mock_sleep_fn.call_count)

    def test_wait_for_all_uploads_to_complete_returns_immediately_when_zero_uploads_are_in_progress(
            self):
        self.mock_files = []

        self.waiter.wait_for_all_uploads_to_complete()

        self.assertFalse(self.mock_sleep_fn.called)

    def test_wait_for_all_uploads_to_complete_waits_for_all_uploads_to_reach_100(
            self):
        self.mock_files = [
            {
                u'uploadprogress': 90,
            },
            {
                u'uploadprogress': 91,
            },
            {
                u'uploadprogress': 92,
            },
            {
                u'uploadprogress': 93,
            },
            {
                u'uploadprogress': 94,
            },
        ]
        self.mock_sleep_fn.side_effect = lambda _: self.increment_upload_progress_by_one()

        self.waiter.wait_for_all_uploads_to_complete()

        self.assertEqual(100 - 90, self.mock_sleep_fn.call_count)
