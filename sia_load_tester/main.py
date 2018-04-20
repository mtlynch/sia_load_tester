#!/usr/bin/python2

import argparse
import os
import logging
import threading
import time

import contracts
import dataset
import dataset_uploader
import jobs
import preconditions
import progress
import state
import upload_queue

logger = logging.getLogger(__name__)


def configure_logging(output_dir):
    root_logger = logging.getLogger()
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(
        os.path.join(output_dir, 'sia_load_test.log'))
    formatter = logging.Formatter(
        '%(asctime)s %(name)-16s %(levelname)-4s %(message)s',
        '%Y-%m-%d %H:%M:%SZ')
    formatter.converter = time.gmtime
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)


def main(args):
    _ensure_directory_exists(args.output_dir)
    configure_logging(args.output_dir)
    logger.info('Started runnning')

    preconditions.check()

    snapshotter = state.make_snapshotter(args.output_dir)
    snapshotter.snapshot()

    contracts.ensure_min_contracts()

    input_dataset = dataset.load_from_path(args.dataset_root)
    upload_jobs = jobs.from_dataset(input_dataset, args.dataset_copies)
    queue = upload_queue.from_upload_jobs(upload_jobs)

    exit_event = threading.Event()
    progress.start_monitor_async(exit_event)

    uploader = dataset_uploader.make_dataset_uploader(queue, exit_event)
    uploader.upload()

    snapshotter.snapshot()
    logger.info('Test completed successfully')


def _ensure_directory_exists(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Sia Load Tester',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-i',
        '--dataset_root',
        required=True,
        help='Path to root directory of data to upload to Sia')
    parser.add_argument(
        '-n',
        '--dataset_copies',
        default=1,
        type=int,
        help='The number of times to upload each input file to Sia')
    parser.add_argument(
        '-o',
        '--output_dir',
        required=True,
        help='Path to directory for test output files')
    main(parser.parse_args())
