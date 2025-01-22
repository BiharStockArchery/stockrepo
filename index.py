import yfinance as yf
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import os
import pytz
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# Read stock symbols from a CSV file
def load_symbols_from_csv(csv_path):
    try:
        # Load the CSV file containing stock symbols
        df = pd.read_csv(csv_path)
        # Assuming the CSV has a column named 'Symbol'
        symbols = df['Symbol'].apply(lambda x: f"{x}.NS").tolist()  # Append .NS to each symbol
        return symbols
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []

# Path to your CSV file
csv_path = "C:/Users/Anupam/Desktop/New folder (3)/stocks.csv"  # Replace with your actual CSV file path

# Load symbols from CSV and append ".NS"
symbols = load_symbols_from_csv(csv_path)

# Define the timezone (Indian Standard Time)
IST = pytz.timezone('Asia/Kolkata')

def get_sector_data():
    try:
        # Get the current date and time
        now = datetime.now(IST)

        # Fetch 5 days of minute-level data to get the high, low, and previous day's close prices
        data = yf.download(symbols, period="5d", interval="1d")  # 5-day data to get high, low, and close
        
        # Debugging: Print fetched data
        print("Fetched data:\n", data)

        # Check if the data contains 'Adj Close' or 'Close' for accurate price info
        stock_data = data.get('Adj Close', data.get('Close'))

        if stock_data is None or stock_data.empty:
            print("Error: No valid stock data for symbols.")
            return {"error": "No valid stock data available."}

        # Prepare the result data dictionary
        result_data = {}

        # Loop through the stock symbols and calculate data for each
        for symbol in symbols:
            # Get the previous day's closing price (last row in 'Adj Close' or 'Close' column)
            previous_day_close = stock_data[symbol].iloc[-2]  # Previous day's closing price
            
            # Get the current day's last close price (for comparison)
            current_price = stock_data[symbol].iloc[-1]  # Today's most recent price (last row)

            # Calculate the percentage change from the previous day's close price
            percentage_change = ((current_price - previous_day_close) / previous_day_close) * 100

            # Add the stock data to the result
            result_data[symbol] = {
                "current_price": current_price,
                "percentage_change": percentage_change
            }

        return result_data

    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}

# Define the background task function
def update_sector_data():
    print("Running background task to update sector data...")
    sector_data = get_sector_data()
    print("Sector data updated:", sector_data)

@app.route('/sector-heatmap')
def sector_heatmap():
    sector_data = get_sector_data()

    if "error" in sector_data:
        return jsonify({"status": "error", "message": sector_data["error"]}), 400

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
