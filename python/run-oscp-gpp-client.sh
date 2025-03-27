#!/bin/bash
CUR_DIR=$(pwd)

# Set these variables:
IMAGE_PATH=$CUR_DIR/../data/lamar/ios_2022-01-12_16.32.48_000_14911412476/14911412476.jpg
IMAGESTXT_PATH=$CUR_DIR/../data/lamar/ios_2022-01-12_16.32.48_000_14911412476/images.txt
SENSORS_PATH=$CUR_DIR/../data/lamar/ios_2022-01-12_16.32.48_000_14911412476/sensors.txt
BT_PATH=$CUR_DIR/../data/lamar/ios_2022-01-12_16.32.48_000_14911412476/bt.txt
WIFI_PATH=$CUR_DIR/../data/lamar/ios_2022-01-12_16.32.48_000_14911412476/wifi.txt

TRAJ_PATJ=$CUR_DIR/../data/lamar/ios_2022-01-12_16.32.48_000_14911412476/trajectories.txt

OUT_PATH=$CUR_DIR/../data/lamar/out

# CAMERA_PARAMS_PATH=$CUR_DIR/../data/seattle_camera_params.json
# GEOLOCATION_PARAMS_PATH=$CUR_DIR/../data/seattle_geolocation_params.json

# python demo_client.py $IMAGE_PATH $CAMERA_PARAMS_PATH $GEOLOCATION_PARAMS_PATH
python demo_client.py --image $IMAGE_PATH --imagestxt $IMAGESTXT_PATH --sensors $SENSORS_PATH --bt $BT_PATH --wifi $WIFI_PATH --trajectories $TRAJ_PATJ --output $OUT_PATH
