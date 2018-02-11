#!/usr/bin/python2

import argparse
import logging

import contracts
import dataset
import dataset_uploader
import preconditions
import upload_queue

logger = logging.getLogger(__name__)


def configure_logging():
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-16s %(levelname)-4s %(message)s',
        '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def main(args):
    configure_logging()
    logger.info('Started runnning')
    preconditions.check()
    contracts.ensure_min_contracts()
    input_dataset = dataset.load_from_path(args.dataset_root)
    queue = upload_queue.from_dataset(input_dataset)
    # TODO(mtlynch): Create upload queue.
    uploader = dataset_uploader.make_dataset_uploader(queue)
    uploader.upload()
    # TODO(mtlynch): Dump state.
    logger.info('Test completed successfully')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Sia Load Tester',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-i',
        '--dataset_root',
        required=True,
        help='Path to root directory of data to upload to Sia')
    main(parser.parse_args())
