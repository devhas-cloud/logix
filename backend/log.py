from flask import Flask, send_from_directory, jsonify, request
import os
from dotenv import load_dotenv

# === Load env ===
env_path = "/opt/logix/config/env"
if not load_dotenv(dotenv_path=env_path):
    print(f"❌ env file not found at {env_path}")
    exit(1)

LOG_FILES = {
    'web': '/opt/logix/logs/web.log',
    'sensor': '/opt/logix/logs/sensor.log',
    'send': '/opt/logix/logs/send.log',
    'retry': '/opt/logix/logs/retry.log',
    'backup': '/opt/logix/logs/backup.log',
    'gpio': '/opt/logix/logs/gpio.log',
    'has': '/opt/logix/logs/has-send.log'
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")

PORT_NUMBER_LOG = int(os.getenv('PORT_NUMBER_LOG', '3000'))

app = Flask(__name__, static_folder=None)

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "log.html")

@app.route("/<path:filename>")
def serve_frontend_assets(filename):
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/tail')
def tail_log():
    log_name = request.args.get('log')
    filepath = LOG_FILES.get(log_name)

    if not filepath or not os.path.exists(filepath):
        return jsonify(["Invalid or missing log file."])

    # Baca semua baris
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Ambil hanya 500 baris terakhir
    last_lines = lines[-500:]

    # Hapus isi lama dan tulis ulang hanya 500 baris terakhir
    with open(filepath, 'w') as f:
        f.writelines(last_lines)

    return jsonify(last_lines)

@app.route('/loglist')
def get_log_list():
    return jsonify(list(LOG_FILES.keys()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT_NUMBER_LOG, debug=True, threaded=True)
