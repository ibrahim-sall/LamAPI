from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import subprocess
import os
import json
import re
from collections import OrderedDict

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

selected_folder = os.getcwd()
image_path = os.path.join(selected_folder, '/data/lamar/ios_2022-01-12_16.32.48_000_14911412476/14911412476.jpg')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/upload-image', methods=['POST'])
def upload_image():
    global image_path
    if 'image' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    image_path = filepath  # Stocke le chemin
    return jsonify({'message': 'Image uploadée', 'filename': filename})

@app.route('/set-folder', methods=['POST'])
def set_folder():
    global selected_folder
    if 'files' not in request.files:
        return jsonify({'error': 'Aucun fichier reçu'}), 400

    files = request.files.getlist('files')

    # On extrait le nom du dossier parent à partir du chemin relatif du premier fichier
    first_file_path = files[0].filename
    folder_name = first_file_path.split('/')[0]  # ex: ios_2022-01-12_16.32.48_000_14911412476

    # Création du dossier de destination dans "uploads"
    uploads_base = os.path.join(os.getcwd(), 'uploads')
    target_folder = os.path.join(uploads_base, folder_name)
    os.makedirs(target_folder, exist_ok=True)

    for file in files:
        relative_path = file.filename  # contient le chemin relatif comme "folder/sensors.txt"
        destination_path = os.path.join(uploads_base, relative_path)
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        file.save(destination_path)

    selected_folder = target_folder

    return jsonify({'message': 'Fichiers enregistrés', 'folder': folder_name})

@app.route('/run-bash', methods=['GET'])
def run_bash_command():
    try:
        imagestxt_path = os.path.join(selected_folder, 'images.txt')
        sensors_path = os.path.join(selected_folder, 'sensors.txt')
        bt_path = os.path.join(selected_folder, 'bt.txt')
        wifi_path = os.path.join(selected_folder, 'wifi.txt')
        traj_path = os.path.join(selected_folder, 'trajectories.txt')
        out_path = os.path.join(os.getcwd(), 'data', 'lamar', 'out')

        command = [
            'python3', 'demo_client.py',
            '--image', image_path,
            '--imagestxt', imagestxt_path,
            '--sensors', sensors_path,
            '--bt', bt_path,
            '--wifi', wifi_path,
            '--trajectories', traj_path,
            '--output', out_path
        ]

        result = subprocess.run(command, capture_output=True, text=True)
        print(result)
        if result.returncode != 0:
            return jsonify({
                'error': 'La commande a échoué',
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }), 500

        # Split the output by lines
        output_lines = result.stdout.splitlines()
        
        # Let's attempt to parse the first line as JSON
        try:
            json_str = output_lines[1].strip()  # Assuming output_lines[1] contains the JSON string
            print("JSON string:", json_str)  # Add debug print for the JSON string
            
            # Attempt to clean and parse the JSON
            json_str = re.sub(r'\s*([-+]?\d*\.\d+|\d+)\s*', r'\1', json_str)  # Clean the numbers
            json_data = json.loads(json_str) 

            if isinstance(json_data.get('geopose', {}).get('position', {}).get('h'), str):
                json_data['geopose']['position']['h'] = float(json_data['geopose']['position']['h'])
            if isinstance(json_data.get('geopose', {}).get('position', {}).get('lat'), str):
                json_data['geopose']['position']['lat'] = float(json_data['geopose']['position']['lat'])
            if isinstance(json_data.get('geopose', {}).get('position', {}).get('lon'), str):
                json_data['geopose']['position']['lon'] = float(json_data['geopose']['position']['lon'])
            
            # Convert quaternion values to float (if not already)
            for key in ['w', 'x', 'y', 'z']:
                if isinstance(json_data.get('geopose', {}).get('quaternion', {}).get(key), str):
                    json_data['geopose']['quaternion'][key] = float(json_data['geopose']['quaternion'][key])
        except Exception as e:
            return jsonify({
                'error': 'Erreur de décodage JSON',
                'message': str(e)
            }), 500
        

        # Utilisation d'OrderedDict pour garantir l'ordre des clés
        ordered_data = {'type':json_data.get('type'),'id':json_data.get('id'),'timestamp':json_data.get('timestamp'),'geopose':json_data.get('geopose')}

        # Renvoie le JSON avec l'ordre des clés souhaité
        return ordered_data
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
