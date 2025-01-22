import yfinance as yf
from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

# List of sector-wise stock symbols from NSE
symbols = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ACC.NS", "APLAPOLLO.NS", "AUBANK.NS", "AARTIIND.NS",
    # Add more symbols here...
]

def get_sector_data():
    result_data = {}

    for symbol in symbols:
        try:
            print(f"Fetching data for {symbol}...")
            # Fetch today's data (1 day interval)
            data = yf.download(symbol, period="1d", interval="1m")  # Fetching minute-level data for today

            # Ensure data is available
            if data.empty:
                print(f"Warning: No data returned for {symbol}")
                continue

            # Get today's opening price (first row) and current price (last row)
            opening_price = data['Open'].iloc[0]
            current_price = data['Adj Close'].iloc[-1]  # The most recent price

            # Calculate the percentage change between opening price and current price
            percentage_change = ((current_price - opening_price) / opening_price) * 100

            # Add the stock data to the result
            result_data[symbol] = {
                "opening_price": opening_price,
                "current_price": current_price,
                "percentage_change": percentage_change
            }

        except ValueError as e:
            print(f"Error processing symbol {symbol}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error processing symbol {symbol}: {str(e)}")
            time.sleep(2)  # Adding a small delay before retrying

    return result_data

@app.route('/sector-heatmap')
def sector_heatmap():
    sector_data = get_sector_data()

    if not sector_data:
        return jsonify({"status": "error", "message": "No valid stock data available."}), 400

    return jsonify({"status": "success", "data": sector_data})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
