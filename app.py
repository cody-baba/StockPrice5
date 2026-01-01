import requests
from flask import Flask, request, Response
from datetime import datetime
from xml.sax.saxutils import escape

app = Flask(__name__)

# Hardcoded Alpha Vantage API key
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

def intraday(symbol, interval="5min"):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={API_KEY}"
    data = av_get(url)
    ts, o, h, l, c = latest_from_series(data, f"Time Series ({interval})")
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c}

def daily(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    ts, o, h, l, c = latest_from_series(data, "Time Series (Daily)")
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c}

def weekly(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    ts, o, h, l, c = latest_from_series(data, "Weekly Time Series")
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c}

def monthly(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    ts, o, h, l, c = latest_from_series(data, "Monthly Time Series")
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c}

def tag(name, content):
    if content is None:
        return f"<{name}/>"
    return f"<{name}>{escape(str(content))}</{name}>"

def xml_unified(symbol, intraday_v, daily_v, weekly_v, monthly_v):
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
        '<daily>',
        tag("open", daily_v["open"]),
        tag("high", daily_v["high"]),
        tag("low", daily_v["low"]),
        tag("close", daily_v["close"]),
        tag("timestamp", daily_v["timestamp"]),
        '</daily>',
        '<weekly>',
        tag("open", weekly_v["open"]),
        tag("high", weekly_v["high"]),
        tag("low", weekly_v["low"]),
        tag("close", weekly_v["close"]),
        tag("timestamp", weekly_v["timestamp"]),
        '</weekly>',
        '<monthly>',
        tag("open", monthly_v["open"]),
        tag("high", monthly_v["high"]),
        tag("low", monthly_v["low"]),
        tag("close", monthly_v["close"]),
        tag("timestamp", monthly_v["timestamp"]),
        '</monthly>',
        '<meta>',
        tag("source", "Alpha Vantage"),
        tag("generatedAt", datetime.utcnow().isoformat() + "Z"),
        '</meta>',
        '</hkStock>'
    ]
    return "\n".join(xml)

@app.route("/hk/quote.xml", methods=["GET"])
def unified_xml():
    symbol = request.args.get("symbol", "0700.HK")
    try:
        intraday_v = intraday(symbol)
        daily_v = daily(symbol)
        weekly_v = weekly(symbol)
        monthly_v = monthly(symbol)
        xml = xml_unified(symbol, intraday_v, daily_v, weekly_v, monthly_v)
        return Response(xml, mimetype="application/xml")
    except Exception as e:
        err = f'<?xml version="1.0" encoding="UTF-8"?><error>{escape(str(e))}</error>'
        return Response(err, status=502, mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
