import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import pytz

def get_exact_epoch_times():
    # Get the current date
    today = datetime.now().date()
    
    # Define the start and end times for the exact 45-minute interval
    start_time = datetime.combine(today, datetime.strptime("01:45", "%H:%M").time())
    end_time = start_time + timedelta(minutes=45)  # Three 15-minute candles
    
    # Convert to epoch (seconds since epoch)
    start_epoch = int(start_time.timestamp())
    end_epoch = int(end_time.timestamp())
    
    return start_epoch, end_epoch

def get_data(start_epoch, end_epoch):
    url = "https://public.coindcx.com/market_data/candlesticks"
    query_params = {
        "pair": "B-ETH_USDT",
        "from": start_epoch,
        "to": end_epoch,
        "resolution": "15m",  # '1' OR '5' OR '60' OR '1D'
        "pcode": "f"
    }
    response = requests.get(url, params=query_params)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
    else:
        return (f"Error: {response.status_code}, {response.text}")

# Get epoch times for the specified period
start_epoch, end_epoch = get_exact_epoch_times()
print("Start Epoch:", start_epoch)
print("End Epoch:", end_epoch)

# Fetch the data
data = get_data(start_epoch, end_epoch)

# Check if data was successfully retrieved and has candles
if isinstance(data, dict) and 'data' in data:
    candles = data['data']
    
    # Exclude the last candle (potentially incomplete)
    if len(candles) > 1:
        candles = candles[:-1]

    # Convert the data to a DataFrame
    df = pd.DataFrame(candles)

    # Convert time from milliseconds to datetime and localize it
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df['time'] = df['time'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')  # Localize to UTC and convert to desired timezone
    df.set_index('time', inplace=True)

    # Plot the candlestick chart
    mpf.plot(df, type='candle', style='charles', title='Candlestick Chart', ylabel='Price')
    plt.show()
else:
    print("Error retrieving data or no data available")
