from fastapi import FastAPI, Query
import requests
from typing import Optional, List
from datetime import datetime

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
    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()
    return r.json()

@app.get("/indicators")
def get_indicators(
    symbol: str = Query(..., description="Stock symbol, e.g. IBM, AAPL, 0700.HK"),
    interval: str = Query("daily", description="Interval: daily, weekly, etc."),
    days: Optional[int] = Query(1, description="Number of latest days to return")
):
    # Fetch all three indicators
    sma = fetch_indicator("SMA", symbol, interval, time_period=10)
    macd = fetch_indicator("MACD", symbol, interval)
    rsi = fetch_indicator("RSI", symbol, interval, time_period=14)

    sma_data = sma.get("Technical Analysis: SMA", {})
    macd_data = macd.get("Technical Analysis: MACD", {})
    rsi_data = rsi.get("Technical Analysis: RSI", {})

    # Collect all available dates
    all_dates = set(sma_data.keys()) & set(macd_data.keys()) & set(rsi_data.keys())
    sorted_dates = sorted(all_dates, reverse=True)

    # Limit to latest X days
    selected_dates = sorted_dates[:days]

    results: List[dict] = []
    for date in selected_dates:
        results.append({
            "date": date,
            "stock": symbol,
            "sma": sma_data[date]["SMA"],
            "macd": macd_data[date]["MACD"],
            "macd_signal": macd_data[date]["MACD_Signal"],
            "macd_hist": macd_data[date]["MACD_Hist"],
            "rsi": rsi_data[date]["RSI"]
        })

    return {"symbol": symbol, "interval": interval, "results": results}
