import matplotlib
matplotlib.use('Agg')

from flask import Flask, request, render_template, jsonify
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)


# 📊 Fetch stock data
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")

    if hist.empty:
        return None

    # Moving averages
    hist["MA50"] = hist["Close"].rolling(window=50).mean()
    hist["MA200"] = hist["Close"].rolling(window=200).mean()

    latest = hist.iloc[-1]
    previous = hist.iloc[-2]

    price_change = latest["Close"] - previous["Close"]
    percent_change = (price_change / previous["Close"]) * 100

    return {
        "current_price": round(latest["Close"], 2),
        "open_price": round(latest["Open"], 2),
        "previous_close": round(previous["Close"], 2),
        "price_change": round(price_change, 2),
        "percent_change": round(percent_change, 2),
        "history": hist
    }


# 📈 Generate chart with indicators
def get_stock_chart(ticker, hist):
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(hist.index, hist["Close"], label="Close Price")
    ax.plot(hist.index, hist["MA50"], label="50-day MA")
    ax.plot(hist.index, hist["MA200"], label="200-day MA")

    ax.set_title(f"{ticker} - Stock Analysis")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    img_b64 = base64.b64encode(img.read()).decode('utf-8')
    plt.close(fig)

    return img_b64


# 📊 Simple rule-based analysis (no AI)
def get_basic_analysis(data):
    if data["percent_change"] > 1:
        trend = "Bullish 📈"
    elif data["percent_change"] < -1:
        trend = "Bearish 📉"
    else:
        trend = "Sideways ➡️"

    if data["current_price"] > data["previous_close"]:
        signal = "Uptrend"
    else:
        signal = "Downtrend"

    return f"{trend} | {signal}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_stock_info', methods=['POST'])
def get_stock_info():
    ticker = request.form['ticker'].strip().upper()

    try:
        data = get_stock_data(ticker)

        if not data:
            return jsonify({"error": "Invalid ticker or no data found"})

        chart = get_stock_chart(ticker, data["history"])
        analysis = get_basic_analysis(data)

        return jsonify({
            "ticker": ticker,
            "current_price": data["current_price"],
            "open_price": data["open_price"],
            "previous_close": data["previous_close"],
            "price_change": data["price_change"],
            "percent_change": data["percent_change"],
            "analysis": analysis,
            "stock_chart": chart
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

