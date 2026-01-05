from flask import Flask, request, render_template, jsonify
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import io
import base64

app = Flask(__name__)
ALPHA_API_KEY = "CL2GRZLVCKHL2K0W"

def get_stock_chart(ticker):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={ALPHA_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "Time Series (Daily)" not in data:
        return None

    time_series = data["Time Series (Daily)"]
    sorted_dates_str = sorted(time_series.keys())[-250:]  # last 250 trading days
    dates = [datetime.strptime(date, "%Y-%m-%d") for date in sorted_dates_str]
    prices = [float(time_series[date]["4. close"]) for date in sorted_dates_str]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, prices, label="Closing Price", color='blue')

    ax.set_title(f"{ticker} - Stock Price Chart (Last Year)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (INR)")
    ax.grid(True)
    ax.legend()

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_b64 = base64.b64encode(img.read()).decode('utf-8')
    plt.close(fig)

    return img_b64

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_stock_info', methods=['POST'])
def get_stock_info():
    ticker = request.form['ticker'].strip().upper()

    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={ALPHA_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if "Time Series (Daily)" not in data:
            return jsonify({"error": f"Unable to fetch data for {ticker}. Try again later."})

        time_series = data["Time Series (Daily)"]
        sorted_dates = sorted(time_series.keys(), reverse=True)

        latest = time_series[sorted_dates[0]]
        previous = time_series[sorted_dates[1]]

        current_price = latest["4. close"]
        open_price = latest["1. open"]
        previous_close = previous["4. close"]

        stock_chart = get_stock_chart(ticker)

        return jsonify({
            "ticker": ticker,
            "current_price": current_price,
            "open_price": open_price,
            "previous_close": previous_close,
            "stock_chart": stock_chart
        })

    except Exception as e:
        print("Error fetching data:", e)
        return jsonify({"error": "Something went wrong. Try again later."})

if __name__ == "__main__":
    app.run(debug=True)
