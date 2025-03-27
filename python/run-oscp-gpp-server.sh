#!/bin/bash
CUR_DIR=$(pwd)

# Set these variables:
CONFIG_PATH=$CUR_DIR/../data/seattle_vps.json

python demo_server.py --config $CONFIG_PATH
