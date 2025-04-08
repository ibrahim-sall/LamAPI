from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import subprocess
import os

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
        # cur_dir = os.getcwd()
        # bash_script_path = os.path.join(cur_dir, 'run-oscp-gpp-client.sh')
        # result = subprocess.run([bash_script_path], capture_output=True, text=True)
        # return jsonify({'output': result.stdout.strip()})

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

        if result.returncode != 0:
            return jsonify({
                'error': 'La commande a échoué',
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }), 500

        return jsonify({
            'stdout': result.stdout.strip(),
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
