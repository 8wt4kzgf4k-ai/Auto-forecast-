import json
from datetime import datetime
import time
import requests

# ----------------------------
# API CONFIGURATION
# ----------------------------
API_KEY = "b3f898dec7014a23aeddd60f2cb30fc6"  # <-- Add your API key here
BASE_URL = "https://api.twelvedata.com/time_series"
SYMBOL = "EUR/USD"

TIMEFRAMES = ["1min", "3min", "5min", "15min", "30min", "1h"]
HISTORY_LIMIT = 100
FORECAST_FILE = "forecast.json"

# ----------------------------
# Helper functions
# ----------------------------
def get_last_candle_close(tf):
    """
    Fetch last closed candle from Twelve Data
    """
    params = {
        "symbol": SYMBOL,
        "interval": tf,
        "outputsize": 1,
        "apikey": API_KEY
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Twelve Data returns "values" list
        last_close = float(data["values"][0]["close"])
        return last_close
    except Exception as e:
        print(f"Error fetching {tf}: {e}")
        return None

def last_candle_close_time(tf):
    """
    Return timestamp of last closed candle
    """
    params = {
        "symbol": SYMBOL,
        "interval": tf,
        "outputsize": 1,
        "apikey": API_KEY
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data["values"][0]["datetime"]
    except Exception as e:
        print(f"Error fetching candle time {tf}: {e}")
        return datetime.utcnow().isoformat()

def calculate_predicted_price(tf, last_close):
    """
    Example prediction: simple +0.001 or -0.001 based on random trend
    Replace with your ML or indicator logic
    """
    import random
    return round(last_close + random.choice([-0.001,0,0.001]), 5)

# ----------------------------
# Main Loop
# ----------------------------
while True:
    try:
        with open(FORECAST_FILE,"r") as f:
            forecast_data = json.load(f)
    except:
        forecast_data = {}

    for tf in TIMEFRAMES:
        last_close = get_last_candle_close(tf)
        if last_close is None:
            continue  # skip if API failed
        predicted = calculate_predicted_price(tf, last_close)

        if predicted > last_close:
            signal = "Buy"
        elif predicted < last_close:
            signal = "Sell"
        else:
            signal = "Hold"

        last_tf_data = forecast_data.get(tf, [])
        last_signal_data = last_tf_data[-1] if last_tf_data else None
        candle_time = last_candle_close_time(tf)
        forecast_time = datetime.utcnow().isoformat()

        # Only update if new forecast differs
        if (not last_signal_data or 
            last_signal_data["signal"] != signal or 
            last_signal_data["predicted_price"] != predicted):

            entry = {
                "signal": signal,
                "price": last_close,
                "predicted_price": predicted,
                "confidence": 3,
                "meter": "|||",
                "candle_time": candle_time,
                "forecast_time": forecast_time
            }

            forecast_data.setdefault(tf, []).append(entry)
            forecast_data[tf] = forecast_data[tf][-HISTORY_LIMIT:]

    # Save updated forecast
    with open(FORECAST_FILE,"w") as f:
        json.dump(forecast_data, f, indent=4)

    print(f"[{datetime.utcnow().isoformat()}] Forecast updated.")

    # Wait 1 minute
    time.sleep(60)
