import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import os

PAIR = "EURUSD=X"
TIMEFRAMES = ["1M", "3M", "5M", "15M", "30M", "1H"]
MAX_HISTORY = 300
FILE = "forecast.json"

def fetch_data():
    df = yf.download(
        PAIR,
        start=datetime.now() - timedelta(hours=2),
        interval="1m",
        progress=False
    )
    df.reset_index(inplace=True)
    return df

def resample(df, tf):
    tf_map = {"1M":"1T","3M":"3T","5M":"5T","15M":"15T","30M":"30T","1H":"1H"}
    r = df.resample(tf_map[tf], on="Datetime").agg({
        "Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"
    }).dropna()
    r["Return"] = r["Close"].pct_change()
    return r.reset_index()

def confidence(signal, ret):
    bars = 0
    if (signal=="Buy" and ret>0) or (signal=="Sell" and ret<0):
        bars += 1
    if abs(ret) > 0.0001:
        bars += 1
    if abs(ret) > 0.0002:
        bars += 1
    meter = "".join(["█" if i < bars else "░" for i in range(3)])
    return bars, meter

def load():
    if os.path.exists(FILE):
        with open(FILE,"r") as f:
            return json.load(f)
    return {tf:[] for tf in TIMEFRAMES}

def save(data):
    with open(FILE,"w") as f:
        json.dump(data,f,indent=2)

def run():
    df = fetch_data()
    hist = load()

    for tf in TIMEFRAMES:
        r = resample(df, tf)
        if len(r) < 2: continue
        last = r.iloc[-1]
        prev = r.iloc[-2]

        signal = "Buy" if last["Return"] > 0 else "Sell"
        conf, meter = confidence(signal, prev["Return"])

        entry = {
            "time": last["Datetime"].strftime("%Y-%m-%d %H:%M"),
            "price": round(float(last["Close"]),5),
            "signal": signal,
            "confidence": conf,
            "meter": meter
        }

        hist[tf].append(entry)
        hist[tf] = hist[tf][-MAX_HISTORY:]

    save(hist)
    print("forecast.json updated")

if __name__ == "__main__":
    run()
