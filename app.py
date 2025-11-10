from flask import Flask, send_file, jsonify
from pathlib import Path
from refresh import refresh
import os

app = Flask(__name__, static_folder="static")
DATA_DIR = Path("data")

@app.route("/")
def index():
    return send_file(app.static_folder + "/dashboard.html")

@app.route("/api/refresh")
def api_refresh():
    state = refresh()
    return jsonify(state)

@app.route("/state.json")
def state_json():
    return send_file(DATA_DIR / "state.json")

@app.route("/data.csv")
def data_csv():
    return send_file(DATA_DIR / "data.csv")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
