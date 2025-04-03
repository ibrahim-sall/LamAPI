from flask import Flask, jsonify, render_template
import subprocess
import os

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/run-bash', methods=['GET'])
def run_bash_command():
    try:
        # Exemple de commande Bash
        cur_dir = os.getcwd()
        bash_script_path = os.path.join(cur_dir, 'run-oscp-gpp-client.sh')
        result = subprocess.run([bash_script_path], capture_output=True, text=True)
        return jsonify({'output': result.stdout.strip()})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
