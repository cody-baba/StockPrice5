from fastapi import FastAPI, Query
import requests
import xml.etree.ElementTree as ET
from typing import Optional

app = FastAPI()

API_KEY = "5LGQXGL2RBOLEWZK"
BASE_URL = "https://www.alphavantage.co/query"

def fetch_indicator(function: str, symbol: str, interval: str = "daily", **kwargs):
    params = {
        "function": function,
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
        "series_type": "close"
    }
    params.update(kwargs)
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

@app.get("/indicators", response_class=None)
def get_indicators(
    symbol: str = Query(..., description="Stock symbol, e.g. TSLA, AAPL, 0700.HK"),
    interval: str = Query("daily", description="Time interval: daily, weekly, etc."),
    days: Optional[int] = Query(1, description="Number of latest days to return")
):
    # Fetch indicators
    sma_json = fetch_indicator("SMA", symbol, interval, time_period=10)
    macd_json = fetch_indicator("MACD", symbol, interval)
    rsi_json = fetch_indicator("RSI", symbol, interval, time_period=14)

    sma_data = sma_json.get("Technical Analysis: SMA", {})
    macd_data = macd_json.get("Technical Analysis: MACD", {})
    rsi_data = rsi_json.get("Technical Analysis: RSI", {})

    # Get common dates
    common_dates = sorted(set(sma_data) & set(macd_data) & set(rsi_data), reverse=True)
    selected_dates = common_dates[:days]

    # Build XML
    root = ET.Element("Indicators")
    ET.SubElement(root, "Symbol").text = symbol
    ET.SubElement(root, "Interval").text = interval

    for date in selected_dates:
        entry = ET.SubElement(root, "Entry", date=date)
        ET.SubElement(entry, "Stock").text = symbol
        ET.SubElement(entry, "SMA").text = sma_data[date]["SMA"]
        ET.SubElement(entry, "MACD").text = macd_data[date]["MACD"]
        ET.SubElement(entry, "MACD_Signal").text = macd_data[date]["MACD_Signal"]
        ET.SubElement(entry, "MACD_Hist").text = macd_data[date]["MACD_Hist"]
        ET.SubElement(entry, "RSI").text = rsi_data[date]["RSI"]

    return ET.tostring(root, encoding="unicode")
