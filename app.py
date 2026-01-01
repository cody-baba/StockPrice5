import requests
from flask import Flask, request, Response
from datetime import datetime
from xml.sax.saxutils import escape

app = Flask(__name__)
API_KEY = "5LGQXGL2RBOLEWZK"

def av_get(url):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    if "Note" in data or "Error Message" in data:
        raise ValueError(data.get("Note") or data.get("Error Message"))
    return data

def latest_from_series(data, series_key):
    ts = data.get(series_key, {})
    if not ts:
        return None, None, None, None, None
    latest_ts = sorted(ts.keys())[-1]
    row = ts[latest_ts]
    return latest_ts, row.get("1. open"), row.get("2. high"), row.get("3. low"), row.get("4. close")

def slice_series(data, series_key, count):
    ts = data.get(series_key, {})
    if not ts:
        return []
    sorted_keys = sorted(ts.keys(), reverse=True)[:count]
    result = []
    for k in sorted_keys:
        row = ts[k]
        result.append({
            "date": k,
            "open": row.get("1. open"),
            "high": row.get("2. high"),
            "low": row.get("3. low"),
            "close": row.get("4. close")
        })
    return result

def intraday(symbol, interval="5min"):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={API_KEY}"
    data = av_get(url)
    ts, o, h, l, c = latest_from_series(data, f"Time Series ({interval})")
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c}

def daily(symbol, days=5):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    return slice_series(data, "Time Series (Daily)", days)

def weekly(symbol, weeks=4):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    return slice_series(data, "Weekly Time Series", weeks)

def monthly(symbol, months=6):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    return slice_series(data, "Monthly Time Series", months)

def sma(symbol, interval="daily", time_period=10):
    url = f"https://www.alphavantage.co/query?function=SMA&symbol={symbol}&interval={interval}&time_period={time_period}&series_type=close&apikey={API_KEY}"
    data = av_get(url)
    series = data.get("Technical Analysis: SMA", {})
    if not series:
        return {"timestamp": None, "period": time_period, "value": None}
    ts = sorted(series.keys())[-1]
    return {"timestamp": ts, "period": time_period, "value": series[ts].get("SMA")}

def rsi(symbol, interval="daily", time_period=14):
    url = f"https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval={interval}&time_period={time_period}&series_type=close&apikey={API_KEY}"
    data = av_get(url)
    series = data.get("Technical Analysis: RSI", {})
    if not series:
        return {"timestamp": None, "period": time_period, "value": None}
    ts = sorted(series.keys())[-1]
    return {"timestamp": ts, "period": time_period, "value": series[ts].get("RSI")}

def macd(symbol, interval="daily", fastperiod=12, slowperiod=26, signalperiod=9):
    url = f"https://www.alphavantage.co/query?function=MACD&symbol={symbol}&interval={interval}&series_type=close&fastperiod={fastperiod}&slowperiod={slowperiod}&signalperiod={signalperiod}&apikey={API_KEY}"
    data = av_get(url)
    series = data.get("Technical Analysis: MACD", {})
    if not series:
        return {"timestamp": None, "macd": None, "macd_signal": None, "macd_hist": None}
    ts = sorted(series.keys())[-1]
    vals = series[ts]
    return {
        "timestamp": ts,
        "macd": vals.get("MACD"),
        "macd_signal": vals.get("MACD_Signal"),
        "macd_hist": vals.get("MACD_Hist")
    }

def tag(name, content):
    if content is None:
        return f"<{name}/>"
    return f"<{name}>{escape(str(content))}</{name}>"

def xml_unified(symbol, intraday_v, daily_v, weekly_v, monthly_v, sma_v, rsi_v, macd_v):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<hkStock>',
        tag("symbol", symbol),
        '<latest>',
        tag("open", intraday_v["open"]),
        tag("high", intraday_v["high"]),
        tag("low", intraday_v["low"]),
        tag("close", intraday_v["close"]),
        tag("timestamp", intraday_v["timestamp"]),
        '</latest>',
        '<recentDays>'
    ]
    for d in daily_v:
        xml.append(f'<day date="{escape(d["date"])}" open="{escape(str(d["open"]))}" high="{escape(str(d["high"]))}" low="{escape(str(d["low"]))}" close="{escape(str(d["close"]))}"/>')
    xml.append('</recentDays>')
    xml.append('<recentWeeks>')
    for w in weekly_v:
        xml.append(f'<week date="{escape(w["date"])}" open="{escape(str(w["open"]))}" high="{escape(str(w["high"]))}" low="{escape(str(w["low"]))}" close="{escape(str(w["close"]))}"/>')
    xml.append('</recentWeeks>')
    xml.append('<recentMonths>')
    for m in monthly_v:
        xml.append(f'<month date="{escape(m["date"])}" open="{escape(str(m["open"]))}" high="{escape(str(m["high"]))}" low="{escape(str(m["low"]))}" close="{escape(str(m["close"]))}"/>')
    xml.append('</recentMonths>')
    xml.append('<indicators>')
    xml.append(f'<sma period="{sma_v["period"]}" value="{escape(str(sma_v["value"]))}" timestamp="{escape(str(sma_v["timestamp"]))}"/>')
    xml.append(f'<rsi period="{rsi_v["period"]}" value="{escape(str(rsi_v["value"]))}" timestamp="{escape(str(rsi_v["timestamp"]))}"/>')
    xml.append(f'<macd timestamp="{escape(str(macd_v["timestamp"]))}" macd="{escape(str(macd_v["macd"]))}" signal="{escape(str(macd_v["macd_signal"]))}" hist="{escape(str(macd_v["macd_hist"]))}"/>')
    xml.append('</indicators>')
    xml.append('<meta>')
    xml.append(tag("source", "Alpha Vantage"))
    xml.append(tag("generatedAt", datetime.utcnow().isoformat() + "Z"))
    xml.append('</meta>')
    xml.append('</hkStock>')
    return "\n".join(xml)

@app.route("/hk/quote.xml", methods=["GET"])
def unified_xml():
    symbol = request.args.get("symbol", "0700.HK")
    days = int(request.args.get("days", "5"))
    weeks = int(request.args.get("weeks", "4"))
    months = int(request.args.get("months", "6"))
    try:
        intraday_v = intraday(symbol)
        daily_v = daily(symbol, days)
        weekly_v = weekly(symbol, weeks)
        monthly_v = monthly(symbol, months)
        sma_v = sma(symbol)
        rsi_v = rsi(symbol)
        macd_v = macd(symbol)
        xml = xml_unified(symbol, intraday_v, daily_v, weekly_v, monthly_v, sma_v, rsi_v, macd_v)
        return Response(xml, mimetype="application/xml")
    except Exception as e:
        err = f'<?xml version="1.0" encoding="UTF-8"?><error>{escape(str(e))}</error>'
        return Response(err, status=502, mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
