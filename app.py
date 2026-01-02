from fastapi import FastAPI, Query
import requests
import xml.etree.ElementTree as ET

app = FastAPI()

API_KEY = "5LGQXGL2RBOLEWZK"
BASE_URL = "https://www.alphavantage.co/query"

def fetch_indicator(function, symbol, interval="daily", **kwargs):
    params = {
        "function": function,
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
        "series_type": "close"
    }
    params.update(kwargs)
    r = requests.get(BASE_URL, params=params)
    return r.json()

@app.get("/indicators")
def get_indicators(symbol: str = Query(...), interval: str = "daily"):
    sma = fetch_indicator("SMA", symbol, interval, time_period=10)
    macd = fetch_indicator("MACD", symbol, interval)
    rsi = fetch_indicator("RSI", symbol, interval, time_period=14)

    # Build XML response
    root = ET.Element("Indicators")
    ET.SubElement(root, "Symbol").text = symbol
    ET.SubElement(root, "Interval").text = interval

    sma_data = ET.SubElement(root, "SMA")
    for date, values in sma.get("Technical Analysis: SMA", {}).items():
        entry = ET.SubElement(sma_data, "Entry", date=date)
        ET.SubElement(entry, "Value").text = values["SMA"]

    macd_data = ET.SubElement(root, "MACD")
    for date, values in macd.get("Technical Analysis: MACD", {}).items():
        entry = ET.SubElement(macd_data, "Entry", date=date)
        ET.SubElement(entry, "MACD_Signal").text = values["MACD_Signal"]
        ET.SubElement(entry, "MACD").text = values["MACD"]
        ET.SubElement(entry, "MACD_Hist").text = values["MACD_Hist"]

    rsi_data = ET.SubElement(root, "RSI")
    for date, values in rsi.get("Technical Analysis: RSI", {}).items():
        entry = ET.SubElement(rsi_data, "Entry", date=date)
        ET.SubElement(entry, "Value").text = values["RSI"]

    return ET.tostring(root, encoding="unicode")
