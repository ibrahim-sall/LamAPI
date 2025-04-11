# Open AR Cloud GeoPoseProtocol - Python implementation
# Created by Gabor Soros, 2023
#
# Copyright 2023 Nokia
# Licensed under the MIT License
# SPDX-License-Identifier: MIT


from flask import Flask, request, jsonify, make_response, abort, render_template, send_from_directory
from werkzeug.utils import secure_filename
from argparse import ArgumentParser
import base64
import os
import json
from georeference.georef import convert_to_wgs84 
from flask_swagger_ui import get_swaggerui_blueprint
from oscp.geoposeprotocol import *
from demo_docker import *



parser = ArgumentParser()
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
    default='LIN',
    help='Specify the dataset to use between {CAB, LIN, HGE}. Default is "LIN".'
)

args = parser.parse_args()

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')
##############################################
@app.route('/process', methods=['POST'])
def process():
    if 'image' not in request.files or 'files' not in request.files:
        return jsonify({'error': 'Image ou fichiers du dossier manquants'}), 400

    image_file = request.files['image']
    folder_files = request.files.getlist('files')

    try:
        image_path = save_uploaded_image(image_file)
        selected_folder = save_uploaded_folder(folder_files)
        output = run_geopose_processing(image_path, selected_folder)
        return jsonify(output)

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except RuntimeError as re:
        return jsonify({'error': str(re)}), 500
    except Exception as e:
        return jsonify({'error': 'Erreur inattendue', 'message': str(e)}), 500

##############################################

    
def save_uploaded_image(file):
    if file.filename == '':
        raise ValueError("Nom de l’image vide")

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filepath

def save_uploaded_folder(files):
    if not files:
        raise ValueError("Aucun fichier reçu pour le dossier")

    first_path = files[0].filename
    folder_name = first_path.split('/')[0]
    base_path = os.path.join(os.getcwd(), 'uploads')
    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        relative_path = file.filename
        destination = os.path.join(base_path, relative_path)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        file.save(destination)

    return folder_path

def run_geopose_processing(image_path, folder_path):
    imagestxt = os.path.join(folder_path, 'images.txt')
    sensors = os.path.join(folder_path, 'sensors.txt')
    bt = os.path.join(folder_path, 'bt.txt')
    wifi = os.path.join(folder_path, 'wifi.txt')
    traj = os.path.join(folder_path, 'trajectories.txt')
    out = os.path.join(os.getcwd(), 'data', 'lamar', 'out')

    command = [
        'python3', 'demo_client.py',
        '--image', image_path,
        '--imagestxt', imagestxt,
        '--sensors', sensors,
        '--bt', bt,
        '--wifi', wifi,
        '--trajectories', traj,
        '--output', out
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Échec de la commande:\n{result.stderr.strip()}")

    return parse_output_json(result.stdout)

def parse_output_json(stdout_text):
    lines = stdout_text.splitlines()
    if len(lines) < 2:
        raise ValueError("Sortie inattendue du script")

    json_str = lines[1].strip()
    json_str = re.sub(r'\s*([-+]?\d*\.\d+|\d+)\s*', r'\1', json_str)
    data = json.loads(json_str)

    pos = data.get('geopose', {}).get('position', {})
    quat = data.get('geopose', {}).get('quaternion', {})

    for key in ['h', 'lat', 'lon']:
        if isinstance(pos.get(key), str):
            pos[key] = float(pos[key])

    for key in ['w', 'x', 'y', 'z']:
        if isinstance(quat.get(key), str):
            quat[key] = float(quat[key])

    return {
        'type': data.get('type'),
        'id': data.get('id'),
        'timestamp': data.get('timestamp'),
        'geopose': data.get('geopose'),
        'output': stdout_text  # Optionnel
    }


    
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

    write_data(imgdata, geoPoseRequest)
    cmd = create_docker_command_lamar(data_dir=os.getenv("DATA_DIR"), output_dir=args.output_path,scene=args.dataset)
    run_docker_command(cmd)

    POSES_FILE = '/output/' + args.dataset + '/pose_estimation/query_hololens/map/superpoint/superglue/fusion-netvlad-ap-gem-10/triangulation/rig/poses.txt'

    if not os.path.exists(POSES_FILE):
        return make_response(jsonify({"error": "The file './poses.txt' does not exist."}), 500)
    with open(POSES_FILE, "r") as f:
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
  
    geoPose.position.lat, geoPose.position.lon,  geoPose.position.h  = convert_to_wgs84(float(last_line[6]), float(last_line[7]), float(last_line[8]))

    geoPoseResponse = GeoPoseResponse(id = geoPoseRequest.id, timestamp = geoPoseRequest.timestamp)
    geoPoseResponse.geopose = geoPose

    # DEBUG
    #print("Response:")
    #print(geoPoseResponse.toJson())
    #print()

    try:
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
    app.run(host='0.0.0.0', port=5000, debug=True)