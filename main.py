from fastapi import FastAPI
import yfinance as yf
import pandas as pd
import ta

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/indicators/{symbol}")
def indicators(symbol: str, period: str = "3mo", interval: str = "1d"):
    """
    Returns date, symbol, close price, SMA(20), RSI(14), MACD and MACD signal line.
    """
    try:
        # Use yf.download instead of Ticker().history to avoid Yahoo blocking
        hist = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            progress=False,
            threads=False
        )
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

    if hist.empty:
        return {"error": "No data found", "symbol": symbol}

    df = hist.copy()
    df["SMA_20"] = ta.trend.sma_indicator(df["Close"], window=20)
    df["RSI_14"] = ta.momentum.rsi(df["Close"], window=14)
    df["MACD"] = ta.trend.macd(df["Close"])
    df["MACD_signal"] = ta.trend.macd_signal(df["Close"])

    result = []
    for date, row in df.iterrows():
        result.append({
            "date": date.strftime("%Y-%m-%d"),
            "symbol": symbol,
            "close": float(row["Close"]),
            "sma_20": float(row["SMA_20"]) if pd.notna(row["SMA_20"]) else None,
            "rsi_14": float(row["RSI_14"]) if pd.notna(row["RSI_14"]) else None,
            "macd": float(row["MACD"]) if pd.notna(row["MACD"]) else None,
            "macd_signal": float(row["MACD_signal"]) if pd.notna(row["MACD_signal"]) else None
        })

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "indicators": result
    }
