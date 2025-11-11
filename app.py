from flask import Flask, jsonify, render_template_string
import subprocess, json, datetime, os

app = Flask(__name__)

# --- קובץ ה־state.json שאליו נכתוב את הנתונים ---
STATE_PATH = os.path.join(os.getcwd(), "local/data/state.json")

# --- דף HTML נטען ישירות מהקובץ ---
@app.route('/')
def dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())

# --- API שמחזיר את הנתונים האחרונים ---
@app.route('/api/state')
def get_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"timestamp": None, "routers": []}
    return jsonify(data)

# --- כפתור לרענון נתונים בזמן אמת ---
@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    try:
        subprocess.run(["python", "local_refresh_mofet.py"], check=True)
        return jsonify({"success": True, "time": datetime.datetime.now().isoformat()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
@app.route('/api/upload', methods=['POST'])
def upload_state():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "no file"}), 400
    path = os.path.join("local/data", "state.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file.save(path)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

