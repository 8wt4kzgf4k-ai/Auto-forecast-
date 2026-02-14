from flask import Flask, send_from_directory
from datetime import datetime, timezone
import time
import requests
import json
import random
import threading
import os

# ----------------------------
# CONFIGURATION
# ----------------------------
API_KEY = "9dae42e8a6644049bbd811fdbfbf921f"  # Replace with your Twelve Data API key
BASE_URL = "https://api.twelvedata.com/time_series"
SYMBOL = "EUR/USD"

TIMEFRAMES = ["1min","3min","5min","15min","30min","1h"]
HISTORY_LIMIT = 100
FORECAST_FILE = "forecast.json"

app = Flask(__name__)

# ----------------------------
# DATA FETCH
# ----------------------------
def get_last_candle(tf):
    params = {"symbol": SYMBOL, "interval": tf, "outputsize": 3, "apikey": API_KEY}
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        data = r.json()

        if "values" not in data or len(data["values"]) < 3:
            return {"status": "CLOSED", "prices": [], "time": None}

        # API returns newest first
        p2 = float(data["values"][0]["close"])
        p1 = float(data["values"][1]["close"])
        p0 = float(data["values"][2]["close"])

        candle_time = datetime.fromisoformat(
            data["values"][0]["datetime"]
        ).astimezone(timezone.utc).isoformat()

        return {"status": "OPEN", "prices": [p0,p1,p2], "time": candle_time}
    except Exception as e:
        print(f"Fetch error {tf}: {e}")
        return {"status": "ERROR", "prices": [], "time": None}

def calculate_predicted_price(price):
    # Placeholder prediction logic; replace with your model
    return round(price + random.choice([-0.001,0,0.001]), 5)

# ----------------------------
# FORECAST LOOP
# ----------------------------
def forecast_loop():
    while True:
        try:
            if os.path.exists(FORECAST_FILE):
                with open(FORECAST_FILE,"r") as f:
                    forecast_data = json.load(f)
            else:
                forecast_data = {}
        except:
            forecast_data = {}

        for tf in TIMEFRAMES:
            result = get_last_candle(tf)
            last_tf_data = forecast_data.get(tf, [])
            last_entry = last_tf_data[-1] if last_tf_data else None
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

            # MARKET CLOSED
            if result["status"] == "CLOSED":
                last_price = last_entry["price"] if last_entry else None
                entry = {
                    "signal": "MARKET CLOSED",
                    "reversal": False,
                    "acceleration": "N/A",
                    "price": last_price,
                    "predicted_price": last_price,
                    "confidence": 0,
                    "meter": "---",
                    "candle_time": last_entry["candle_time"] if last_entry else None,
                    "forecast_time": now_utc
                }
                forecast_data.setdefault(tf, []).append(entry)
                forecast_data[tf] = forecast_data[tf][-HISTORY_LIMIT:]
                continue

            if result["status"] != "OPEN":
                continue

            p0, p1, p2 = result["prices"]

            # Velocity & acceleration
            v = p2 - p1
            a = (p2 - p1) - (p1 - p0)

            if v > 0 and a > 0:
                accel_state = "ACCELERATING UP"
            elif v > 0 and a < 0:
                accel_state = "UP BUT SLOWING"
            elif v < 0 and a < 0:
                accel_state = "ACCELERATING DOWN"
            elif v < 0 and a > 0:
                accel_state = "DOWN BUT SLOWING"
            else:
                accel_state = "FLAT"

            last_close = p2
            candle_time = result["time"]
            predicted = calculate_predicted_price(last_close)

            signal = "Buy" if predicted > last_close else "Sell" if predicted < last_close else "Hold"

            # Reversal detection
            reversal = False
            if last_entry:
                if (last_entry["signal"]=="Buy" and signal=="Sell") or (last_entry["signal"]=="Sell" and signal=="Buy"):
                    reversal = True

            if not last_entry or last_entry["signal"] != signal or last_entry["predicted_price"] != predicted:
                entry = {
                    "signal": signal,
                    "reversal": reversal,
                    "acceleration": accel_state,
                    "price": last_close,
                    "predicted_price": predicted,
                    "confidence": 3,
                    "meter": "|||",
                    "candle_time": candle_time,
                    "forecast_time": now_utc
                }
                forecast_data.setdefault(tf, []).append(entry)
                forecast_data[tf] = forecast_data[tf][-HISTORY_LIMIT:]

        with open(FORECAST_FILE,"w") as f:
            json.dump(forecast_data,f,indent=4)

        print(f"[{datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()}] Forecast updated.")
        time.sleep(60)  # fetch new candle every 1 min

# ----------------------------
# FLASK ROUTES
# ----------------------------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/forecast.json")
def forecast_json():
    return send_from_directory(".", FORECAST_FILE)

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=forecast_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
