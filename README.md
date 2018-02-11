# Sia Load Tester

[![Build Status](https://travis-ci.org/mtlynch/sia_load_tester.svg?branch=master)](https://travis-ci.org/mtlynch/sia_load_tester)
[![Coverage Status](https://coveralls.io/repos/github/mtlynch/sia_load_tester/badge.svg?branch=master)](https://coveralls.io/github/mtlynch/sia_load_tester?branch=master)

## Overview

A load tester for Sia.

## Performing a load test

### Generating dummy data

To generate simulated data, you can use the [dummy_file_generator](https://github.com/mtlynch/dummy_file_generator):

```bash
# Target directory and file prefix for output files.
OUTPUT_PREFIX="~/sia-load-test-data/$(date --utc +"%Y-%m-%dT%H%M%SZ")-"

# Minimum amount of data to generate.
TOTAL_DATA_SIZE=1099511627776 # 1 TB

# Get the file generator
git clone https://github.com/mtlynch/dummy_file_generator.git
cd dummy_file_generator
```

#### Optimal case

To test Sia's optimal case, generate files of 41942760 bytes each:

```bash
SIZE_PER_FILE=41942760 # ~40 MiB

python dummy_file_generator/main.py \
  --size_per_file "$SIZE_PER_FILE" \
  --total_size "$TOTAL_DATA_SIZE" \
  --output_prefix "$OUTPUT_PREFIX"
```

#### Worst case

To test Sia's worst case, generate files of 1 byte each:

```bash
SIZE_PER_FILE=1

python dummy_file_generator/main.py \
  --size_per_file "$SIZE_PER_FILE" \
  --total_size "$TOTAL_DATA_SIZE" \
  --output_prefix "$OUTPUT_PREFIX"
```

### Start load test

You can run the load test using an existing directory or by generating dummy data (see above). Specify the data directory using the `--dataset_root` flag. The load tester will find all files in the directory recursively and upload all files in that directory that have not already been uploaded to Sia.

```bash
# Specify the directory in which the upload test data is located.
DATASET_ROOT=~/sia-load-test-data

git clone https://github.com/mtlynch/sia_load_tester.git
cd sia_load_tester
python sia_load_tester\main.py \
  --dataset_root "$DATASET_ROOT"
```
