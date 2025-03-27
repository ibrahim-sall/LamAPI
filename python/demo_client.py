# Open AR Cloud GeoPoseProtocol - Python implementation
# Created by Gabor Soros, 2023
#
# Copyright 2023 Nokia
# Licensed under the MIT License
# SPDX-License-Identifier: MIT
#
# Created based on the protocol definition:
# https://github.com/OpenArCloud/oscp-geopose-protocol
# and the JavaScript implementation:
# https://github.com/OpenArCloud/gpp-access/


from PIL import Image
from oscp.geoposeprotocol import *
import time
import json
import base64
import requests
from argparse import ArgumentParser
from datetime import datetime, timezone


###print(json.dumps(GeoPoseRequest(), default=lambda o: o.__dict__))


parser = ArgumentParser()
parser.add_argument(
    '--url', '-url',
    type=str,
    default='http://127.0.0.1:8080/geopose'
)
parser.add_argument(
    '--image', '-image',
    type=str,
    required = True,
    default = None
)
parser.add_argument(
    '--imagestxt', '-imagestxt',
    type=str,
    required = True,
    default = None
)
parser.add_argument(
    '--sensors', '-sensors',
    type=str,
    required = True,
    default = None
)
parser.add_argument(
    '--bt', '-bt',
    type=str,
    required = True,
    default = None
)
parser.add_argument(
    '--wifi', '-wifi',
    type=str,
    required = True,
    default = None
)
parser.add_argument(
    '--trajectories', '-trajectories',
    type=str,
    required = True,
    default = None
)
args=parser.parse_args()


with open(args.image, 'rb') as f:
    image = f.read()
    image_base64 = base64.b64encode(image).decode('utf-8')
    f.close()

# open it again with PIL just to find out its size
image = Image.open(args.image)

with open(args.imagestxt, 'r') as f:
    lines = f.read().splitlines()[1:]  # skip header
    f.close()

images_config = [line.strip().split(', ') for line in lines][0]
print("Image config:")
print(images_config)

with open(args.sensors, 'r') as f:
    lines = f.read().splitlines()[1:]
    f.close()

sensors_config = [line.strip().split(', ') for line in lines]
print("Sensors config:")
print(sensors_config)

with open(args.bt, 'r') as f:
    lines = f.read().splitlines()[1:]
    f.close()

bt_config = [line.strip().split(', ') for line in lines]
print("Bluetooth config:")
print(bt_config)

with open(args.wifi, 'r') as f:
    lines = f.read().splitlines()[1:]
    f.close()

wifi_config = [line.strip().split(', ') for line in lines]
print("Wifi config:")
print(wifi_config)

with open(args.trajectories, 'r') as f:
    lines = f.read().splitlines()[1:]
    f.close()

trajectories_config = [line.strip().split(', ') for line in lines]
print("Trajectories config:")
print(trajectories_config)


kCameraSensorId = images_config[1]
cameraReading = CameraReading(sensorId=kCameraSensorId)
cameraReading.timestamp = images_config[0]
cameraReading.sensorId = kCameraSensorId
cameraReading.imageFormat = ImageFormat.RGBA32
cameraReading.size = [image.width, image.height]
cameraReading.imageBytes = image_base64
cameraReading.sequenceNumber = 1
cameraReading.imageOrientation = ImageOrientation()
cameraReading.params.model = sensors_config[0][3]
cameraReading.params.modelParams = sensors_config[0][4:]
# cameraReading.params = CameraParameters(model=camera_config["camera_model"], modelParams=camera_config["camera_params"])

# kGeolocationSensorId = "my_gps_sensor"
# geolocationReading = GeolocationReading(sensorId=kGeolocationSensorId)
# geolocationReading.timestamp = datetime.now(timezone.utc).timestamp()*1000 # milliseconds since epoch
# geolocationReading.latitude = geolocation_config["lat"]
# geolocationReading.longitude = geolocation_config["lon"]
# geolocationReading.altitude = geolocation_config["h"]

kBluetoothSensorId = bt_config[0][1]
bluetoothReading = BluetoothReading(sensorId=kBluetoothSensorId)
bluetoothReading.timestamp = bt_config[0][0]
bluetoothReading.RSSI = [bt_config[i][3] for i in range(0,len(bt_config))]

geoPoseRequest = GeoPoseRequest()
geoPoseRequest.timestamp = datetime.now(timezone.utc).timestamp()*1000 # milliseconds since epoch
geoPoseRequest.sensors.append(Sensor(type = SensorType.CAMERA, id=kCameraSensorId, name=sensors_config[0][1], model=sensors_config[0][3]))
geoPoseRequest.sensorReadings.cameraReadings.append(cameraReading)
geoPoseRequest.sensors.append(Sensor(type = SensorType.BLUETOOTH, id=kBluetoothSensorId))
geoPoseRequest.sensorReadings.bluetoothReadings.append(bluetoothReading)
# geoPoseRequest.sensors.append(Sensor(type = SensorType.GEOLOCATION, id=kGeolocationSensorId))
# geoPoseRequest.sensorReadings.geolocationReadings.append(geolocationReading)

try:
    headers = {"Content-Type":"application/json"}
    body = geoPoseRequest.toJson()

    # DEBUG
    geoPoseRequest.sensorReadings.cameraReadings[0].imageBytes = "<IMAGE_BASE64>"
    print("Request (without image):")
    print(geoPoseRequest.toJson())
    print()

    response = requests.post(args.url, headers=headers, data=body)
    print(f'Status: {response.status_code}')
    jdata = response.json()
    geoPoseResponse = GeoPoseResponse.fromJson(jdata)

    # DEBUG:
    print("Response:")
    print(geoPoseResponse.toJson())
    print()

except Exception as e:
    print(f'err: {e}')
