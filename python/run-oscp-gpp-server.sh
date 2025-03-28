#!/bin/bash
CUR_DIR=$(pwd)

# Set these variables:
CONFIG_PATH=$CUR_DIR/../data/seattle_vps.json

OUT_PATH=$CUR_DIR/../data/lamar/OUT

python demo_server.py --config $CONFIG_PATH -output_path $OUT_PATH
