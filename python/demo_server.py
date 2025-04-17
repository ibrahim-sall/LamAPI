# Open AR Cloud GeoPoseProtocol - Python implementation
# Created by Gabor Soros, 2023
#
# Copyright 2023 Nokia
# Licensed under the MIT License
# SPDX-License-Identifier: MIT


from flask import Flask, request, jsonify, make_response, abort, render_template
from argparse import ArgumentParser
from georeference.georef import convert_to_wgs84 
from flask_swagger_ui import get_swaggerui_blueprint
from oscp.geoposeprotocol import *
import numpy as np
import requests

from server_func.demo_docker import *
from server_func.to_capture import *
# from server_func.write_capture import *
from server_func.celery_worker import celery
from celery import shared_task
from celery.result import AsyncResult


app = Flask(__name__)

upload_folder = configure_upload_folder()

@app.route('/')
def home():
    return render_template('index.html')

##############################################

@app.route('/process', methods=['POST'])
def process():
    app.logger.info("Processing request started.")

    if 'image' not in request.files or 'files' not in request.files:
        app.logger.error("Missing 'image' or 'files' in request.")
        return jsonify({'error': 'Image ou fichiers du dossier manquants'}), 400

    image_file = request.files['image']
    folder_files = request.files.getlist('files')

    if not image_file or len(folder_files) == 0:
        app.logger.error("Image file or folder files are empty.")
        return jsonify({'error': 'Image ou fichiers du dossier manquants'}), 400

    try:
        app.logger.info("Saving uploaded image.")
        image_path = save_uploaded_image(image_file, upload_folder)
        app.logger.info(f"Image saved at: {image_path}")

        app.logger.info("Saving uploaded folder files.")
        selected_folder = save_uploaded_folder(folder_files)
        app.logger.info(f"Folder files saved at: {selected_folder}")

        app.logger.info("Running GeoPose processing.")
        output = run_geopose_processing(image_path, selected_folder)

        if not isinstance(output, dict):
            raise ValueError("Invalid output from GeoPose processing. Expected a dictionary.")

        app.logger.info(f"GeoPose processing output: {output}")
    except Exception as e:
        app.logger.error(f"Error during image or folder processing: {e}")
        return jsonify({'error': 'Erreur lors du traitement de l\'image ou des fichiers', 'message': str(e)}), 500

    try:
        app.logger.info("Sending POST request to /geopose endpoint.")
        response = requests.post('http://127.0.0.1:5000/geopose', json=output)

        if response.status_code != 202:
            app.logger.error(f"Error from /geopose endpoint: {response.status_code}, {response.text}")
            return jsonify({'error': 'Erreur lors de la requête à /geopose', 'message': response.text}), response.status_code

        app.logger.info(f"Response from /geopose: {response.status_code}, {response.json()}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        app.logger.error(f"Unexpected error during /geopose request: {e}")
        return jsonify({'error': 'Erreur inattendue', 'message': str(e)}), 500

##############################################
    
# Swagger UI route
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "LamAPI",
        'additionalQueryStringParams': {
            'config': '.',  
            'output': 'path/volume_output'  
        }
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

##################################################

@app.route('/geopose', methods=['GET'])
def status():
    return make_response("{\"status\": \"running\"}", 200)

@app.route('/geopose', methods=['POST'])
def localize():
    jdata = request.get_json()

    task = process_geopose_task.apply_async(args=[jdata])

    return jsonify({"task_id": task.id}), 202

@shared_task(name='process_geopose_task')
def process_geopose_task(jdata):
    geoPoseRequest = GeoPoseRequest.fromJson(jdata)

    if len(geoPoseRequest.sensorReadings.cameraReadings) < 1:
        abort(400, description='request has no camera readings')
    if geoPoseRequest.sensorReadings.cameraReadings[0].imageBytes is None:
        abort(400, description='request has no image')
    imgdata = base64.b64decode(geoPoseRequest.sensorReadings.cameraReadings[0].imageBytes)

    try:
        print("Starting to write data...")
        write_data(imgdata, geoPoseRequest)
        print("Data writing completed successfully.")
    except Exception as e:
        print(f"Error during data writing: {e}")
        raise

    try:
        print("Preparing to run Docker command...")

        docker_run, cmd = command(data_dir=os.getenv("DATA_DIR"), output_dir=os.getenv("OUTPUT_DIR"), query_id=f"query_{geoPoseRequest.id}", scene=os.getenv("SCENE"))
        print(f"Docker run command: {docker_run}")
        print(f"Command to execute: {cmd}")
        run(docker_run, cmd)
    except Exception as e:
        print(f"Error during Docker command execution: {e}")
        raise
    scene = os.getenv("SCENE")
    poses_path = f"/output/{scene}/pose_estimation/query_{geoPoseRequest.id}/map/superpoint/superglue/fusion-netvlad-ap-gem-10/triangulation/single_image/poses.txt"

    if not os.path.exists(poses_path ):
        return make_response(jsonify({"error": "The file './poses.txt' does not exist."}), 500)
    with open(poses_path , "r") as f:
        f.seek(0, 2)
        while f.tell() > 0:
            f.seek(f.tell() - 2, 0)
            char = f.read(1)
            if char == '\n':
                break
        last_line = f.readline().strip().split(',')

    geoPose = GeoPose()
    geoPose.quaternion.x = last_line[3]
    geoPose.quaternion.y = last_line[4]
    geoPose.quaternion.z = last_line[5]
    geoPose.quaternion.w = last_line[2]
    ###Convertt to WGS84
  
    geoPose.position.lat, geoPose.position.lon,  geoPose.position.h  = convert_to_wgs84(np.array([float(last_line[6]), float(last_line[7]), float(last_line[8])]))

    geoPoseResponse = GeoPoseResponse(id = geoPoseRequest.id, timestamp = geoPoseRequest.timestamp)
    geoPoseResponse.geopose = geoPose

    print("Response:")
    print(geoPoseResponse.toJson())

    try:
        response = make_response(geoPoseResponse.toJson(), 200)
    except Exception as e:
        print(f"Error writing data: {e}")
        response = make_response(jsonify({"error": "Failed to write data"}), 500)
    return response

@app.route('/geopose/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'error': str(task.info) 
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }

    return jsonify(response)

def write_data(imgdata, geo_pose_request):
    """
    Écrit les données d'image et les lectures des capteurs dans le répertoire de sortie.

    Args:
        imgdata (bytes): Les données de l'image en bytes.
        geo_pose_request (GeoPoseRequest): La requête GeoPose contenant les lectures des capteurs.
    """

    justId = geo_pose_request.sensorReadings.cameraReadings[0].sensorId.split("/")[0]

    try:
        data_dir, scene = os.getenv("DATA_DIR"), os.getenv("SCENE")
        output_dir = f"{data_dir}/{scene}/sessions/query_{geo_pose_request.id}"
        proc_dir = f"{output_dir}/proc"
        raw_dir = f"{output_dir}/raw_data/{justId}/images"
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(proc_dir, exist_ok=True)
        os.makedirs(raw_dir, exist_ok=True)
        print(f"Répertoire créé : {output_dir}")
    except Exception as e:
        print(f"Erreur lors de la création du répertoire : {e}")
        raise

    # Création fichier subsessions
    query_path = f"{proc_dir}/subsessions.txt"
    with open(query_path, "w") as query_file:
        query_file.write(f"{justId}\n")

    try:
        image_path = f"{raw_dir}/{geo_pose_request.sensorReadings.cameraReadings[0].timestamp}.jpg"
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
                f"{reading.timestamp}, {reading.sensorId}, {justId}/images/{reading.timestamp}.jpg\n"
            ]
        }
    }

    for attribute, details in sensor_readings.items():
        file_path = f"{output_dir}/{details['filename']}"
        readings = getattr(geo_pose_request.sensorReadings, attribute, [])

        if readings or attribute == "cameraReadings":
            print(f"Traitement des données pour {attribute} :")
            try:
                with open(file_path, 'w', encoding='utf-8') as sensor_file:
                    sensor_file.write(details['header'])
                    if readings:
                        for reading in readings:
                            lines = details['line_format'](reading)
                            sensor_file.writelines(lines)
                    print(f"Fichier écrit : {file_path}")
            except Exception as e:
                print(f"Erreur lors de l'écriture du fichier {details['filename']} : {e}")
                raise
        else:
            print(f"Aucune donnée trouvée pour {attribute}, fichier ignoré.")

    # Création fichier queries
    query_path = f"{output_dir}/queries.txt"
    with open(query_path, "w") as query_file:
        query_file.write(f"{geo_pose_request.sensorReadings.cameraReadings[0].timestamp}, {geo_pose_request.sensorReadings.cameraReadings[0].sensorId}\n")

    # Création fichier sensors
    query_path = f"{output_dir}/sensors.txt"
    with open(query_path, 'w') as sensor_file:
        sensor_file.write("# sensor_id, name, sensor_type, [sensor_params]+\n")

        if hasattr(geo_pose_request.sensorReadings, "cameraReadings") and geo_pose_request.sensorReadings.cameraReadings:
            cam = geo_pose_request.sensorReadings.cameraReadings[0]

            sensor_id = cam.sensorId
            name = f"phone camera for timestamp {cam.timestamp}"
            sensor_type = "camera"
            width, height = cam.size if cam.size else (0, 0)
            model = cam.params.model if hasattr(cam.params, "model") else ""
            params = cam.params.modelParams if hasattr(cam.params, "modelParams") else ""

            param_str = ', '.join(str(p) for p in params)
            cam_line = f"{sensor_id}, {name}, {sensor_type}, {model}, {width}, {height}"
            if param_str:
                cam_line += f", {param_str}"
            cam_line += "\n"

            sensor_file.write(cam_line)

        # Check if 'sensors' attribute exists before accessing it
        if hasattr(geo_pose_request, "sensors") and geo_pose_request.sensors:
            for sensor in geo_pose_request.sensors:
                if hasattr(sensor, "type") and sensor.type == SensorType.BLUETOOTH:
                    bt_line = f"{sensor.id}, Apple bluetooth sensor, bluetooth\n"
                    sensor_file.write(bt_line)

        return f"query_{geo_pose_request.id}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)