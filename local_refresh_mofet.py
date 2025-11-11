import csv, datetime as dt, json, requests
from pathlib import Path

# === קריאת רשימת נתבים ===
with open("routers.json", "r", encoding="utf-8") as f:
    ROUTERS = json.load(f)

OUT_DIR = Path("local/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "state.json"
OUT_CSV = OUT_DIR / "data.csv"

# === כתובת יעד של השרת שלך ב-Render ===
RENDER_UPLOAD_URL = "https://mofet-dashboard.onrender.com/api/upload"  # שנה לכתובת שלך אם שונה

def find_used_limit(obj):
    """חיפוש שדות data_used ו-data_limit ב-JSON"""
    if isinstance(obj, dict):
        if "data_used" in obj and "data_limit" in obj:
            try:
                return int(float(obj["data_used"])), int(float(obj["data_limit"]))
            except Exception:
                return None
        for v in obj.values():
            res = find_used_limit(v)
            if res:
                return res
    elif isinstance(obj, list):
        for v in obj:
            res = find_used_limit(v)
            if res:
                return res
    return None


def fetch_router_data(router):
    base_url = router["base_url"]
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "mofet-dashboard/1.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "X-CSRF-PROTECTION": "1",
        "Origin": base_url,
        "Referer": f"{base_url}/"
    })

    print(f"\nמתחבר לנתב {router['id']}...")
    r = sess.post(f"{base_url}/api/login", json={"username": router["user"], "password": router["password"]}, timeout=15)
    if r.status_code != 200:
        raise SystemExit(f"Login failed ({r.status_code}) for {router['id']}")

    token = None
    try:
        j = r.json()
        token = (j.get("data") or {}).get("token") or j.get("token")
    except Exception:
        pass
    token = token or sess.cookies.get("token")
    if not token:
        sess.get(base_url, timeout=10)
        token = sess.cookies.get("token")
    if not token:
        raise SystemExit(f"לא מצאתי token עבור הנתב {router['id']}")

    sess.cookies.set("token", token)

    payload = {
        "data": [
            {"endpoint": "/api/data_limit/status", "method": "GET"},
            {"endpoint": "/api/modems/status", "method": "GET"},
            {"endpoint": "/api/date_time/ntp/client/config", "method": "GET"},
            {"endpoint": "/api/sim_switch/config", "method": "GET"},
            {"endpoint": "/api/interfaces/config", "method": "GET"}
        ]
    }

    resp = sess.post(f"{base_url}/api/bulk", json=payload, timeout=20)
    if resp.status_code not in (200, 207):
        raise SystemExit(f"הבקשה ל-bulk נכשלה ({resp.status_code}) עבור {router['id']}")

    data = resp.json()
    return find_used_limit(data)


# === מעבר על כל הנתבים ===
ts = dt.datetime.utcnow().isoformat() + "Z"
routers_state = []
hdr_needed = not OUT_CSV.exists()

with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if hdr_needed:
        w.writerow(["timestamp_utc", "router_id", "data_used_bytes", "data_limit_bytes", "percent"])

    for r in ROUTERS:
        try:
            result = fetch_router_data(r)
            if not result:
                print(f"⚠️ לא נמצאו נתונים עבור {r['id']}")
                continue
            used, limit = result
            pct = round(100 * used / limit, 2)
            routers_state.append({"id": r["id"], "used_bytes": used, "limit_bytes": limit, "percent": pct})
            w.writerow([ts, r["id"], used, limit, pct])
            print(f"✅ {r['id']}: {used:,}/{limit:,} bytes ({pct}%)")
        except Exception as e:
            print(f"❌ שגיאה בנתב {r['id']}: {e}")

# === כתיבה ל-JSON המאוחד ===
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump({"timestamp": ts, "routers": routers_state}, f, ensure_ascii=False, indent=2)

print("\n✅ כל הנתבים עודכנו בהצלחה!")

# === שליחה לשרת Render ===
try:
    with open(OUT_JSON, "rb") as f:
        res = requests.post(RENDER_UPLOAD_URL, files={"file": f}, timeout=15)
    if res.status_code == 200:
        print("📤 הנתונים הועלו בהצלחה לשרת Render.")
    else:
        print(f"⚠️ שגיאה בשליחה לשרת Render: {res.status_code} {res.text}")
except Exception as e:
    print(f"❌ שגיאה בשליחה לשרת Render: {e}")
