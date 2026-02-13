import requests
import json
import os
from datetime import datetime, timedelta
import time

# -----------------------------
# CONFIG
# -----------------------------
API_KEY = "b3f898dec7014a23aeddd60f2cb30fc6"
PAIR = "EUR/USD"
TIMEFRAMES = ["1min","3min","5min","15min","30min","1h"]
MAX_HISTORY = 300
JSON_FILE = "forecast.json"

# -----------------------------
def fetch_candles(tf):
    url = f"https://api.twelvedata.com/time_series?symbol={PAIR}&interval={tf}&outputsize=100&apikey={API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code} error for {tf}")
    data = r.json()
    if "values" not in data:
        raise Exception(f"No values returned for {tf}: {data}")
    # newest last
    candles = list(reversed(data["values"]))
    return candles

# -----------------------------
def fetch_indicator(indicator, tf):
    url = f"https://api.twelvedata.com/{indicator}?symbol={PAIR}&interval={tf}&apikey={API_KEY}&outputsize=100"
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code} error for {indicator} {tf}")
    data = r.json()
    if "values" not in data:
        raise Exception(f"No values returned for {indicator} {tf}: {data}")
    return list(reversed(data["values"]))

# -----------------------------
def load_history():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE,"r") as f:
                return json.load(f)
        except:
            return {tf: [] for tf in TIMEFRAMES}
    return {tf: [] for tf in TIMEFRAMES}

def save_history(data):
    with open(JSON_FILE,"w") as f:
        json.dump(data, f, indent=2)

# -----------------------------
def confidence_meter(signal, last_return, rsi):
    confidence = 0
    if (signal=="Buy" and last_return>0) or (signal=="Sell" and last_return<0):
        confidence += 1
    if rsi:
        if (signal=="Buy" and float(rsi)<70) or (signal=="Sell" and float(rsi)>30):
            confidence += 1
    meter = "".join(["█" if i<confidence else "░" for i in range(3)])
    return confidence, meter

# -----------------------------
def generate_forecast():
    history = load_history()

    for tf in TIMEFRAMES:
        try:
            candles = fetch_candles(tf)
            if len(candles)<2:
                continue

            # last candle data
            last = candles[-1]
            prev = candles[-2]

            close_price = float(last["close"])
            last_return = float(last["close"])/float(prev["close"])-1

            # Simple signal example
            signal = "Buy" if last_return>0 else "Sell"

            # Fetch RSI for confidence (optional, free tier limits!)
            try:
                rsi_data = fetch_indicator("rsi", tf)
                rsi_value = float(rsi_data[-1]["rsi"])
            except:
                rsi_value = None

            confidence, meter = confidence_meter(signal, last_return, rsi_value)

            entry = {
                "time": last["datetime"],
                "price": round(close_price,5),
                "signal": signal,
                "confidence": confidence,
                "meter": meter
            }

            # Append to history
            if tf not in history:
                history[tf] = []
            history[tf].append(entry)
            history[tf] = history[tf][-MAX_HISTORY:]

            # Respect 8 calls/min free tier
            time.sleep(8)  # 1 call every 8 seconds max = ~7-8 calls per min

        except Exception as e:
            print(f"Error for {tf}: {e}")

    save_history(history)
    print("forecast.json updated")

# -----------------------------
if __name__ == "__main__":
    generate_forecast()
