from flask import Flask, jsonify, render_template
import subprocess

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/run-bash', methods=['GET'])
def run_bash_command():
    try:
        # Exemple de commande Bash
        result = subprocess.run(["/home/formation/projet/LamAPI/python/run-oscp-gpp-client.sh"], capture_output=True, text=True)
        return jsonify({'output': result.stdout.strip()})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
