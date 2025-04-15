import base64
import os
import json
import re
import subprocess
from werkzeug.utils import secure_filename

def configure_upload_folder(folder_name='uploads'):
    upload_path = os.path.join(os.getcwd(), folder_name)
    os.makedirs(upload_path, exist_ok=True)
    return upload_path

def save_uploaded_image(file, upload_folder):
    if file.filename == '':
        raise ValueError("Nom de l’image vide")

    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
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
        'python3', '/app/demo_client.py',
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
        raise RuntimeError(f"La commande a échoué:\n{result.stderr.strip()}")

    return parse_output_json(result.stdout)

def parse_output_json(stdout_text):
    lines = stdout_text.splitlines()

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