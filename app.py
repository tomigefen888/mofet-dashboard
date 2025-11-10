from flask import Flask, send_file, jsonify
import json, subprocess, os

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('dashboard.html')

@app.route('/refresh')
def refresh_data():
    try:
        subprocess.run(["python3", "local_refresh_mofet.py"], check=True)
        with open("local/data/state.json", encoding="utf-8") as f:
            state = json.load(f)
        return jsonify({"status": "ok", "state": state})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route('/data')
def get_data():
    try:
        with open("local/data/state.json", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
