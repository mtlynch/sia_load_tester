# Sia Load Tester

[![Build Status](https://travis-ci.org/mtlynch/sia_load_tester.svg?branch=master)](https://travis-ci.org/mtlynch/sia_load_tester)
[![Coverage Status](https://coveralls.io/repos/github/mtlynch/sia_load_tester/badge.svg?branch=master)](https://coveralls.io/github/mtlynch/sia_load_tester?branch=master)

## Overview

A load tester for Sia.

## Pre-requisites

You must have the following installed on your test machine:

* Python 2.7
* git
* Sia 1.x
* A Sia wallet funded with at least 400 SC

The load test is platform-agnostic and will work on any system that provides a Python 2.7 environment. The examples below use Windows PowerShell syntax because that is what I used for the actual test.

## Installation

```ps
# Directory in which to install tools for Sia load test.
$Env:SIA_TOOLS_DIR="c:\sia-tools"
mkdir $ENV:SIA_TOOLS_DIR
cd $ENV:SIA_TOOLS_DIR

git clone https://github.com/mtlynch/dummy_file_generator.git

git clone https://github.com/mtlynch/sia_metrics_collector.git
pushd sia_metrics_collector
pip install -r requirements.txt
popd

git clone https://github.com/mtlynch/sia_load_tester.git
pushd .\sia_load_tester\
pip install -r requirements.txt
popd
```

```ps
$Env:SIA_TEST_ROOT="D:\sia-test"
mkdir $Env:SIA_TEST_ROOT

$Env:SIA_TEST_OUTPUT="$Env:SIA_TEST_ROOT\test-output"
mkdir $Env:SIA_TEST_OUTPUT

$Env:SIA_UPLOAD_DATA_DIR="$Env:SIA_TEST_ROOT\data"
```

## Performing a load test


### Step 1: Generate dummy data (optional)

To perform the load test, you will need data to upload to Sia.

To generate simulated data, you can use the [dummy_file_generator](https://github.com/mtlynch/dummy_file_generator).

#### Optimal case

To test Sia's optimal case, generate files of 41942760 bytes each:

```ps
# Target directory and file prefix for output files.
$Env:OUTPUT_PREFIX="$Env:SIA_UPLOAD_DATA_DIR\optimal-case-40MiB-files\dummy-"

$Env:SIZE_PER_FILE="41942760"         # ~40 MiB
$Env:TOTAL_DATA_SIZE="10995116277760" # 10 TiB

python ""$Env:SIA_TOOLS_DIR\dummy_file_generator\dummy_file_generator\main.py" `
  --size_per_file "$Env:SIZE_PER_FILE" `
  --total_size "$Env:TOTAL_DATA_SIZE" `
  --output_prefix "$Env:$OUTPUT_PREFIX"
```

#### Worst case

To test Sia's worst case, generate files of 1 byte each:

```ps
# Target directory and file prefix for output files.
$Env:OUTPUT_PREFIX="$Env:SIA_UPLOAD_DATA_DIR\worst-case-1B-files\dummy-"

$Env:SIZE_PER_FILE="1"          # 1 byte
$Env:TOTAL_DATA_SIZE="250000"   # ~244 KiB

python "$Env:SIA_TOOLS_DIR\dummy_file_generator\dummy_file_generator\main.py" `
  --size_per_file "$Env:SIZE_PER_FILE" `
  --total_size "$Env:TOTAL_DATA_SIZE" `
  --output_prefix "$Env:OUTPUT_PREFIX"
```

### Step 2: Prepare Sia

In a separate terminal window, start the siad command-line daemon:

```ps
.\siad --modules cgtwr
```

Use siac to unlock your wallet.

```ps
.\siac wallet unlock
```

You don't need to create renter contracts, as the load tester will automatically allocate your full wallet balance to renter contracts when the test begins.

### Step 3: Start Sia metrics collector (optional)

The Sia metrics collector regularly polls Sia to gather metrics about its performance. It's not strictly necessary to the load test, but it captures useful data about Sia's behavior.

```ps
python "$Env:SIA_TOOLS_DIR\sia_metrics_collector\sia_metrics_collector\main.py"`
  --poll_frequency 60 `
  --output_file "$Env:SIA_TEST_OUTPUT\metrics.csv"
```

### Start load tester

You can run the load test using an existing directory or by generating dummy data (see above).

Specify the data directory using the `--dataset_root` flag. The load tester will find all files in the directory recursively and upload all files in that directory that have not already been uploaded to Sia.

```ps
# Specify the directory in which the upload test data is located.

python "$Env:SIA_TOOLS_DIR\sia_load_tester\sia_load_tester\main.py"`
  --dataset_root $Env:SIA_UPLOAD_DATA_DIR `
  --output_dir $Env:SIA_TEST_OUTPUT
```
