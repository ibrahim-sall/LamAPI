# Open AR Cloud GeoPoseProtocol - Python implementation
# Created by Gabor Soros, 2023
#
# Copyright 2023 Nokia
# Licensed under the MIT License
# SPDX-License-Identifier: MIT


from flask import Flask, request, jsonify, make_response, abort
from argparse import ArgumentParser
import base64
import os
import json
from oscp.geoposeprotocol import *
from demo_docker import *

parser = ArgumentParser()
parser.add_argument(
    '--config', '-config',
    type=str,
    required = True,
    default = None
)
parser.add_argument(
    '--output_path', '-output_path',
    type=str,
    required=True,
    default='/mnt/lamas/OUT',
    help='Specify the output path for the results. Default is "/mnt/lamas/OUT".'
)
parser.add_argument(
    '--dataset', '-dataset',
    type=str,
    required=False,
    default='CAB',
    help='Specify the dataset to use between {CAB, LIN, HGE}. Default is "CAB".'
)

args = parser.parse_args()

with open(args.config, 'r') as f:
    config = json.load(f)
    f.close()
print("Server config:")
print(config)


app = Flask(__name__)

@app.route('/geopose', methods=['GET'])
def status():
    return make_response("{\"status\": \"running\"}", 200)


@app.route('/geopose', methods=['POST'])
def localize():
    jdata = request.get_json()
    geoPoseRequest = GeoPoseRequest.fromJson(jdata)

    if len(geoPoseRequest.sensorReadings.cameraReadings) < 1:
        abort(400, description='request has no camera readings')
    if geoPoseRequest.sensorReadings.cameraReadings[0].imageBytes is None:
        abort(400, description='request has no image')
    imgdata = base64.b64decode(geoPoseRequest.sensorReadings.cameraReadings[0].imageBytes)
    # DEBUG
    #print("Request:")
    #print(geoPoseRequest.toJson())
    #print()


    # TODO:
    # ...
    # here comes the call to VPS implementation
    # ...
    # right now we just fill in the example values provided in the config file
    geoPose = GeoPose()
    geoPose.quaternion.x = config["geopose"]["quaternion"]["x"]
    geoPose.quaternion.y = config["geopose"]["quaternion"]["y"]
    geoPose.quaternion.z = config["geopose"]["quaternion"]["z"]
    geoPose.quaternion.w = config["geopose"]["quaternion"]["w"]
    geoPose.position.lat = config["geopose"]["position"]["lat"]
    geoPose.position.lon = config["geopose"]["position"]["lon"]
    geoPose.position.h = config["geopose"]["position"]["h"]

    geoPoseResponse = GeoPoseResponse(id = geoPoseRequest.id, timestamp = geoPoseRequest.timestamp)
    geoPoseResponse.geopose = geoPose

    # DEBUG
    #print("Response:")
    #print(geoPoseResponse.toJson())
    #print()

    try:
        write_data(imgdata, geoPoseRequest)
        cmd = create_docker_command_lamar(data_dir=os.getenv("DATA_DIR"), output_dir=args.output_path,scene=args.dataset)
        run_docker_command(cmd)
        response = make_response(geoPoseResponse.toJson(), 200)
    except Exception as e:
        print(f"Error writing data: {e}")
        response = make_response(jsonify({"error": "Failed to write data"}), 500)
    return response

def write_data(imgdata, geo_pose_request):
    """
    Écrit les données d'image et les lectures des capteurs dans le répertoire de sortie.

    Args:
        imgdata (bytes): Les données de l'image en bytes.
        geo_pose_request (GeoPoseRequest): La requête GeoPose contenant les lectures des capteurs.
    """
    try:
        output_dir = f"{args.output_path}/{geo_pose_request.timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        print(f"Répertoire créé : {output_dir}")
    except Exception as e:
        print(f"Erreur lors de la création du répertoire : {e}")
        raise

    try:
        image_path = f"{output_dir}/{geo_pose_request.timestamp}.png"
        with open(image_path, 'wb') as image_file:
            image_file.write(imgdata)
            print(f"Image écrite : {image_path}")
    except Exception as e:
        print(f"Erreur lors de l'écriture de l'image : {e}")
        raise

    sensor_readings = {
        "bluetoothReadings": {
            "filename": "bt.txt",
            "header": "# timestamp, sensor_id, mac_addr, rssi_dbm, name\n",
            "line_format": lambda reading: [
                f"{reading.timestamp}, {reading.sensorId}, {mac}, {rssi}, {reading.name or ''}\n"
                for mac, rssi in zip(reading.address, reading.RSSI)
            ]
        },
        "wifiReadings": {
            "filename": "wifi.txt",
            "header": "# timestamp, sensor_id, mac_addr, frequency_khz, rssi_dbm, name, scan_time_start_us, scan_time_end_us\n",
            "line_format": lambda reading: [
                f"{reading.timestamp}, {reading.sensorId}, {bssid}, {freq}, {rssi}, {reading.SSID or ''}, {start}, {end}\n"
                for bssid, freq, rssi, start, end in zip(
                    reading.BSSID, reading.frequency, reading.RSSI, reading.scanTimeStart, reading.scanTimeEnd
                )
            ]
        },
        "cameraReadings": {
            "filename": "images.txt",
            "header": "# timestamp, sensor_id, image_path\n",
            "line_format": lambda reading: [
                f"{reading.timestamp}, {reading.sensorId}, {output_dir}/{reading.timestamp}.png\n"
            ]
        }
    }

    for attribute, details in sensor_readings.items():
        if hasattr(geo_pose_request.sensorReadings, attribute):
            readings = getattr(geo_pose_request.sensorReadings, attribute)
            if readings:
                print(f"Traitement des données pour {attribute} :")
                try:
                    file_path = f"{output_dir}/{details['filename']}"
                    with open(file_path, 'w', encoding='utf-8') as sensor_file:
                        sensor_file.write(details['header'])
                        for reading in readings:
                            lines = details['line_format'](reading)
                            sensor_file.writelines(lines)
                        print(f"Fichier écrit : {file_path}")
                except Exception as e:
                    print(f"Erreur lors de l'écriture du fichier {details['filename']} : {e}")
                    raise
            else:
                print(f"Aucune donnée trouvée pour {attribute}, fichier ignoré.")

            
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)