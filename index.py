import yfinance as yf
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import os
import pytz
from datetime import datetime, timedelta
import time

app = Flask(__name__)

# List of sector-wise stock symbols from NSE
symbols = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ACC.NS", "APLAPOLLO.NS", "AUBANK.NS", "AARTIIND.NS", 
    # Add more symbols here...
]

# Define the timezone (Indian Standard Time)
IST = pytz.timezone('Asia/Kolkata')

def get_sector_data():
    result_data = {}

    for symbol in symbols:
        try:
            print(f"Fetching data for {symbol}...")
            # Fetch data from Yahoo Finance
            data = yf.download(symbol, period="5d", interval="1d")

            # Check if data is returned
            if data.empty:
                raise ValueError(f"No data returned for {symbol}")

            # Get the previous day's closing price (second to last row)
            previous_day_close = data['Adj Close'].iloc[-2]  
            current_price = data['Adj Close'].iloc[-1]  # Today's most recent price (last row)

            # Calculate the percentage change from the previous day's close price
            percentage_change = ((current_price - previous_day_close) / previous_day_close) * 100

            # Add the stock data to the result
            result_data[symbol] = {
                "current_price": current_price,
                "percentage_change": percentage_change
            }

        except ValueError as e:
            print(f"Error processing symbol {symbol}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error processing symbol {symbol}: {str(e)}")
            time.sleep(2)  # Adding a small delay before retrying

    return result_data

# Define the background task function
def update_sector_data():
    print("Running background task to update sector data...")
    sector_data = get_sector_data()
    print("Sector data updated:", sector_data)

@app.route('/sector-heatmap')
def sector_heatmap():
    sector_data = get_sector_data()

    if not sector_data:
        return jsonify({"status": "error", "message": "No valid stock data available."}), 400

    return jsonify({"status": "success", "data": sector_data})

if __name__ == '__main__':
    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_sector_data, trigger="interval", seconds=60)  # Run every 60 seconds
    scheduler.start()

    # Ensure Flask is properly shut down with the scheduler
    try:
        port = int(os.environ.get("PORT", 5000))
        app.run(host='0.0.0.0', port=port, debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
