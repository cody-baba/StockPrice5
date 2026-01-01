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

def slice_series(data, series_key, count):
    ts = data.get(series_key, {})
    if not ts or count <= 0:
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

def latest_global_quote(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    quote = data.get("Global Quote", {})
    return {
        "timestamp": quote.get("07. latest trading day"),
        "open": quote.get("02. open"),
        "high": quote.get("03. high"),
        "low": quote.get("04. low"),
        "close": quote.get("05. price")
    }

def fetch_daily(symbol, days):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    return slice_series(data, "Time Series (Daily)", days)

def fetch_weekly(symbol, weeks):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    return slice_series(data, "Weekly Time Series", weeks)

def fetch_monthly(symbol, months):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={symbol}&apikey={API_KEY}"
    data = av_get(url)
    return slice_series(data, "Monthly Time Series", months)

def tag(name, content):
    if content is None:
        return f"<{name}/>"
    return f"<{name}>{escape(str(content))}</{name}>"

def xml_unified(symbol, latest_v, daily_v, weekly_v, monthly_v):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<stock>',
        tag("symbol", symbol),
        '<latest>',
        tag("open", latest_v.get("open")),
        tag("high", latest_v.get("high")),
        tag("low", latest_v.get("low")),
        tag("close", latest_v.get("close")),
        tag("timestamp", latest_v.get("timestamp")),
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
    xml.append('<meta>')
    xml.append(tag("source", "Alpha Vantage"))
    xml.append(tag("generatedAt", datetime.utcnow().isoformat() + "Z"))
    xml.append('</meta>')
    xml.append('</stock>')
    return "\n".join(xml)

@app.route("/quote.xml", methods=["GET"])
def unified_xml():
    symbol = request.args.get("symbol", "TSLA")
    days = int(request.args.get("days", "5"))
    weeks = int(request.args.get("weeks", "4"))
    months = int(request.args.get("months", "6"))
    try:
        latest_v = latest_global_quote(symbol)
        daily_v = fetch_daily(symbol, days)
        weekly_v = fetch_weekly(symbol, weeks)
        monthly_v = fetch_monthly(symbol, months)
        xml = xml_unified(symbol, latest_v, daily_v, weekly_v, monthly_v)
        return Response(xml, mimetype="application/xml")
    except Exception as e:
        err = f'<?xml version="1.0" encoding="UTF-8"?><error>{escape(str(e))}</error>'
        return Response(err, status=502, mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
