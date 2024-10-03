

import yfinance as yf
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime
import seaborn as sns
from datetime import date
st.set_page_config(page_icon=":bar_chart:", layout="wide")
st.title(":bar_chart: AB Tech")
def get_data(symbol, start, end, interval ):
    df = yf.download(symbol, start=start, end=end, interval = interval)   
    # df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    return df

def calculate_sma(data, sma_s, sma_l, ma_type):
    if ma_type == "EMA_SMA":
        data['SMA_S'] = data['Close'].ewm(span=sma_s, adjust=False).mean()
        data['SMA_M'] = data['Close'].rolling(window=sma_l).mean()
        data = data.dropna()
        
    elif ma_type == "SMA_EMA":
        data['SMA_S'] = data['Close'].rolling(window=sma_s).mean()
        data['SMA_M'] = data['Close'].ewm(span=sma_l, adjust=False).mean()
        data = data.dropna()
        
    elif ma_type == "SMA_SMA":
        data['SMA_S'] = data['Close'].rolling(window=sma_s).mean()
        data['SMA_M'] = data['Close'].rolling(window=sma_l).mean()
        data = data.dropna()
        
    elif ma_type == "EMA_EMA":
        data['SMA_S'] = data['Close'].ewm(span=sma_s, adjust=False).mean()
        data['SMA_M'] = data['Close'].ewm(span=sma_l, adjust=False).mean()
        data = data.dropna()
        
    return data

def find_up_down(data):
    up_indices = []
    down_indices = []

    for i in range(1, len(data)):
        # long cond
        if data['SMA_S'][i] > data['SMA_M'][i] and data['SMA_S'][i - 1] <= data['SMA_M'][i - 1]:
            up_indices.append(i)

        if data['SMA_S'][i] < data['SMA_M'][i] and data['SMA_S'][i - 1] >= data['SMA_M'][i - 1]:
            down_indices.append(i)

    return up_indices, down_indices

def analyze_segment(data, up_indices, down_indices):
    merged_indices = sorted(up_indices + down_indices)
    
    segment_types = []
    start_indices = []
    end_indices = []
    reference_close_prices = []
    highest_high_prices = []
    lowest_low_prices = []
    segment_dates = []

    for i in range(len(merged_indices)-1):
        start_idx = merged_indices[i]
        end_idx = merged_indices[i + 1]

        if start_idx in up_indices:
            segment_type = "up"
        else:
            segment_type = "down"

        reference_close_price = data['Close'][start_idx]
        highest_high_price = data['High'][start_idx:end_idx].max()
        lowest_low_price = data['Low'][start_idx:end_idx].min()
        segment_date = data.index[start_idx]

        segment_types.append(segment_type)
        start_indices.append(start_idx)
        end_indices.append(end_idx)
        reference_close_prices.append(reference_close_price)
        highest_high_prices.append(highest_high_price)
        lowest_low_prices.append(lowest_low_price)
        segment_dates.append(segment_date)

    df = pd.DataFrame({
        'Segment Type': segment_types,
        'Start Index': start_indices,
        'End Index': end_indices,
        'Reference Close Price': reference_close_prices,
        'Highest High Price': highest_high_prices,
        'Lowest Low Price': lowest_low_prices,
        'Segment Date': segment_dates
    })
    df['High'] = (df['Highest High Price'] - df['Reference Close Price']) / df['Reference Close Price'] * 100
    df['Low'] = (df['Lowest Low Price'] - df['Reference Close Price']) / df['Reference Close Price'] * 100
    df['up-down'] = df['Reference Close Price'].pct_change() * 100
    df['up-down'].fillna(0, inplace=True)  # Replace NaN values with 0 for the first row
    df["bars taken"] = df["End Index"] - df["Start Index"] 
    df['up-down'] = df['up-down'].shift(-1)
    df['trade_close'] = df['Reference Close Price'].shift(-1)
    df["Returns"] = df["up-down"]
    df.loc[df['Segment Type'] == 'down', 'Returns'] *= -1
    return df

def calculate_profit_loss(df, trade_type, sma_s, sma_l, stop_loss_percent, take_profit_percent, pv):

    long_profit_trades = 0
    long_losses_trades = 0
    short_profit_trades = 0
    short_losses_trades = 0
    long_profit = []
    long_loss = []
    short_profit = []
    short_loss = []
    trades = []
    total_trades = 0
    trade_value = pv
    portfolio_value = 0
    portfolio_values = []
    
    for i in range(len(df)-1):
        if trade_type == "Long":
            if df["Segment Type"][i] == "up":
                
                if df["High"][i] > take_profit_percent:
                    take_profit = trade_value * take_profit_percent / 100
                    portfolio_value += take_profit
                    long_profit_trades += 1
                    long_profit.append(take_profit)
                    trades.append({
                           "Direction": "long",
                           "Status": "✅",
                           "portfolio_value": portfolio_value,
                           "reason" : "Long tp hit"})
                
                elif df["Low"][i] < -(stop_loss_percent):
                    stop_loss = trade_value * stop_loss_percent / 100
                    portfolio_value -= stop_loss
                    long_losses_trades += 1
                    long_loss.append(stop_loss)
                    trades.append({
                           "Direction": "long",
                           "Status": "❌",
                           "portfolio_value": portfolio_value,
                           "reason" : "Long sl hit"})
                    
                else:
                    stop_loss = trade_value * (df["Returns"][i] / 100)
                    portfolio_value += stop_loss
                    long_losses_trades += 1
                    long_loss.append(stop_loss)
                    trades.append({
                           "Direction": "long",
                           "Status": "❌",
                           "portfolio_value": portfolio_value,
                           "reason" : "Long cross "})
                    
                
            total_trades = (long_profit_trades
                            + long_losses_trades)
                
        elif trade_type == "Short":
            if df["Segment Type"][i] == "down":
                if df["Low"][i] < -(take_profit_percent):
                    take_profit = trade_value * take_profit_percent / 100
                    portfolio_value += take_profit
                    short_profit_trades += 1
                    short_profit.append(take_profit)
                    trades.append({
                           "Direction": "short",
                           "Status": "✅",
                           "portfolio_value": portfolio_value,
                           "reason" : "short tp hit"})
                    
                elif df["High"][i] < stop_loss_percent:
                    stop_loss = trade_value * stop_loss_percent / 100
                    portfolio_value -= stop_loss
                    short_losses_trades += 1
                    short_loss.append(stop_loss)
                    trades.append({
                           "Direction": "short",
                           "Status": "❌",
                           "portfolio_value": portfolio_value,
                           "reason" : "short sl hit"})
                    
                else:
                    stop_loss = trade_value * (df["Returns"][i] / 100)
                    portfolio_value -= stop_loss
                    short_losses_trades += 1
                    short_loss.append(stop_loss)
                    trades.append({
                           "Direction": "short",
                           "Status": "❌",
                           "portfolio_value": portfolio_value,
                           "reason" : "short cross"})
                
            total_trades = (short_profit_trades
                            + short_losses_trades)
                
        elif trade_type == "Both":
            if df["Segment Type"][i] == "up":
                if df["High"][i] > take_profit_percent:
                    take_profit = trade_value * take_profit_percent / 100
                    portfolio_value += take_profit
                    long_profit_trades += 1
                    long_profit.append(take_profit)
                    trades.append({
                           "Direction": "long",
                           "Status": "✅",
                           "portfolio_value": portfolio_value,
                           "reason" : "Long tp hit"})
                
                elif df["Low"][i] < -(stop_loss_percent):
                    stop_loss = trade_value * stop_loss_percent / 100
                    portfolio_value -= stop_loss
                    long_losses_trades += 1
                    long_loss.append(stop_loss)
                    trades.append({
                           "Direction": "long",
                           "Status": "❌",
                           "portfolio_value": portfolio_value,
                           "reason" : "Long sl hit"})
                    
                else:
                    stop_loss = trade_value * (df["Returns"][i] / 100)
                    portfolio_value += stop_loss
                    long_losses_trades += 1
                    long_loss.append(stop_loss)
                    trades.append({
                           "Direction": "long",
                           "Status": "❌",
                           "portfolio_value": portfolio_value,
                           "reason" : "Long cross "})
                    

            elif df["Segment Type"][i] == "down":
                if df["Low"][i] < -(take_profit_percent):
                    take_profit = trade_value * take_profit_percent / 100
                    portfolio_value += take_profit
                    short_profit_trades += 1
                    short_profit.append(take_profit)
                    trades.append({
                           "Direction": "short",
                           "Status": "✅",
                           "portfolio_value": portfolio_value,
                           "reason" : "short tp hit"})
                    
                elif df["High"][i] < stop_loss_percent:
                    stop_loss = trade_value * stop_loss_percent / 100
                    portfolio_value -= stop_loss
                    short_losses_trades += 1
                    short_loss.append(stop_loss)
                    trades.append({
                           "Direction": "short",
                           "Status": "❌",
                           "portfolio_value": portfolio_value,
                           "reason" : "short sl hit"})
                    
                else:
                    stop_loss = trade_value * (df["Returns"][i] / 100)
                    portfolio_value -= stop_loss
                    short_losses_trades += 1
                    short_loss.append(stop_loss)
                    trades.append({
                           "Direction": "short",
                           "Status": "❌",
                           "portfolio_value": portfolio_value,
                           "reason" : "short cross"})

            total_trades = (long_profit_trades
                            + long_losses_trades
                            +short_profit_trades
                            + short_losses_trades)
        portfolio_values.append(portfolio_value)

        
    pnl_summary = pd.DataFrame({
        'sma_s': [sma_s],
        'sma_l': [sma_l],
        'trade_type': [trade_type],
        'long_profit_trades': (long_profit_trades),
        'long_losses_trades': (long_losses_trades),
        'short_profit_trades': (short_profit_trades),
        'short_losses_trades': (short_losses_trades),
        'sum_long_profit': sum(long_profit),
        'sum_long_loss': sum(long_loss),
        'sum_short_profit': sum(short_profit),
        'sum_short_loss': sum(short_loss),
        'total_trades': total_trades,
        "portfolio_value" : portfolio_values[-1]
    })
    pnl_portfolio = pd.DataFrame({
        "portfolio_value": portfolio_values,
        })
    trades_df = pd.DataFrame(trades)

    return pnl_summary, pnl_portfolio, trades_df
        

# Streamlit app
def sma_tp_sl():
    # st.set_page_config(page_title="Trading Strategy Dashboard", page_icon=":bar_chart:", layout="wide")
    st.title("Moving Average Trading Analysis")
    guide_placeholder = st.empty()

    # Display the User Guide only if it's the first time the app is loaded
    if 'guide_loaded' not in st.session_state:
        # Display the User Guide
        guide_placeholder.markdown("""
        ---

        ## Moving Average Trading Analysis User Guide

        ### Introduction:

        Welcome to the Moving Average Trading Analysis app! This tool helps you analyze historical stock data and implement a trading strategy based on Moving Averages.

        ### Getting Started:

        1. **User Input:**
        - On the left sidebar, you'll find the "User Input" section. Here, you can customize your analysis by providing the following information:
            - **Symbol (e.g., BTC-USD):** Enter the stock symbol you want to analyze (default: "BTC-USD").
            - **Start Date:** Select the start date for historical data.
            - **End Date:** Select the end date for historical data.
            - **SMA Short Window:** Choose the window size for the Short Simple Moving Average (SMA).
            - **SMA Long Window:** Choose the window size for the Long Simple Moving Average (SMA).
            - **Moving Average Combination:** Select the type of Moving Average combination to use (options: EMA_SMA, SMA_EMA, SMA_SMA, EMA_EMA).
            - **Trade Type:** Choose the trading strategy (options: Long, Short, Both).

        2. **Testing the Analysis:**
        - After entering your preferences, click the "Test" button to initiate the analysis.

        ### Results:

        1. **Historical Data:**
        - The initial section displays the historical data for the selected stock.

        2. **Trading Signals:**
        - A chart is displayed showing the closing price of the stock along with the Short and Long Simple Moving Averages.

        3. **Equity Curve:**
        - An equity curve chart is shown, representing the portfolio value over time based on the trading strategy.

        4. **Returns Chart:**
        - A chart illustrating the returns over time based on the trading strategy.

        5. **Trade Summary:**
        - A bar chart providing a summary of the number of profitable and losing trades for both long and short positions, along with the total number of trades.

        6. **Profit and Loss Summary:**
        - A table summarizing the key statistics of the analysis, including the number of profitable and losing trades, total returns, and more.

        ### Interpreting the Results:

        - **Total Returns:**
        - The total returns percentage is displayed at the top, indicating the overall performance of the selected trading strategy.

        - **Trade Summary:**
        - The bar chart gives a visual representation of the number of profitable and losing trades for both long and short positions.

        - **Profit and Loss Summary:**
        - The table provides detailed statistics on the trading strategy, including the number of trades, profits, losses, and total returns.

        ### Exporting Results:

        - **CSV Export:**
        - The app automatically saves a CSV file containing detailed segment analysis results with the filename format: `<symbol>_sma_<sma_s>_<sma_l>_<ma_type>_<start_date>_<end_date>.csv`.

        ### Conclusion:

        Explore the results and use the information to make informed decisions about your trading strategy. Experiment with different parameters to optimize your approach.

        Happy trading!

        ---

        """)

        # Mark that the user guide has been loaded
        st.session_state.guide_loaded = True
    
    st.sidebar.header("User Input")
    max_date = date.today()
    symbol = st.sidebar.text_input("Enter Symbol (e.g., BTC-USD):", value = "BTC-USD")
    default_start_date = datetime.date(2014, 1, 1)
    start_date = st.sidebar.date_input("Start Date", value = default_start_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_value=max_date)
    interval = st.sidebar.selectbox("select time interval", ["5m","15m", "30m", "1h", "1d"])
    stop_loss_percent = st.sidebar.number_input("enter the stop loss percentage", min_value=0.1, max_value=10.0)
    take_profit_percent = st.sidebar.number_input("enter the take profit percentage", min_value=0.1, max_value=10.0)
    sma_s = st.sidebar.slider("Select SMA Short Window", 1, 100, 21)
    sma_l = st.sidebar.number_input("Select SMA Long Window", 1, 1000, 50)
    pv = st.sidebar.number_input(" enter trade value for each trade ")
    ma_type = st.sidebar.selectbox("Select Moving Average Combination", ["EMA_SMA", "SMA_EMA", "SMA_SMA", "EMA_EMA"])
    trade_type = st.sidebar.radio("Select Trade Type", ["Long", "Short", "Both"])
        
    if st.sidebar.button("Test"):
        if interval == "5m" or interval == "15m" or interval == "30m" or interval == "1h":
            st.write(f"You have selected {interval} so the strategy will be tested for 60 days only due to limitation of yfinance library soon we will work towords this to facilitate the feature so you can test the strategy over a desired date range")
            max_date = date.today()
            start_date = (max_date - timedelta(days=59)).strftime('%Y-%m-%d')
            end_date = max_date
            df = get_data(symbol, start_date, end_date, interval)
        else:
            df = get_data(symbol, start_date, end_date, interval)
        st.subheader("Historical Data")
        st.dataframe(df)

        data = calculate_sma(df, sma_s, sma_l, ma_type)
        up_indices, down_indices = find_up_down(data)
        segments_df = analyze_segment(data, up_indices, down_indices)
        segments_df.to_csv(f"{symbol}_sma_{sma_s}_{sma_l}_{ma_type}_{start_date}_{end_date}.csv", index=False)

        # Display results
        st.subheader("Generating Trade signals And Detailed Trade Report")
        st.dataframe(segments_df)
        # total_returns = segments_df["Returns"].sum()
        # st.info(f"Total Returns: {total_returns} %")

        # Calculate profit and losses
        pnl_summary, pnl_portfolio, trades_df = calculate_profit_loss(segments_df, trade_type, sma_s, sma_l, stop_loss_percent, take_profit_percent, pv)
        total_returns = pnl_summary["portfolio_value"].iloc[0]
        st.subheader("Strategy_performance")
        st.info(f"Total Returns: {total_returns} %")

        # Calculate profit and losses
        # pnl_summary, pnl_portfolio = calculate_profit_losses(segments_df, trade_type, sma_s, sma_l)
        # st.dataframe(pnl_summary)
        st.subheader("Trade_Stasts")
        st.dataframe(pnl_summary)
        st.dataframe(trades_df)
        
        # Display results
        st.subheader("Trading_Signals")
        st.line_chart(data[['Close', 'SMA_S', 'SMA_M']])
        
        st.subheader("Equity_Curve")
        st.line_chart(pnl_portfolio['portfolio_value'])
        
        st.subheader("Returns_chart")
        st.line_chart(segments_df['Returns'])
        
        st.subheader("Trade_summary")
        st.bar_chart(pnl_summary[['long_profit_trades', 'short_profit_trades', 'total_trades']])
        st.sidebar.header("Contact Info")
        st.sidebar.write("Email: work.abtech@gmail.com")
        st.sidebar.write("email us for any feedback & suggestions")



def get_data(symbol, start, end, interval ):
    df = yf.download(symbol, start=start, end=end, interval = interval)   
    return df

def calculate_sma(data, sma_s, sma_l, ma_type):
    if ma_type == "EMA_SMA":
        data['SMA_S'] = data['Close'].ewm(span=sma_s, adjust=False).mean()
        data['SMA_M'] = data['Close'].rolling(window=sma_l).mean()
        data = data.dropna()
        
    elif ma_type == "SMA_EMA":
        data['SMA_S'] = data['Close'].rolling(window=sma_s).mean()
        data['SMA_M'] = data['Close'].ewm(span=sma_l, adjust=False).mean()
        data = data.dropna()
        
    elif ma_type == "SMA_SMA":
        data['SMA_S'] = data['Close'].rolling(window=sma_s).mean()
        data['SMA_M'] = data['Close'].rolling(window=sma_l).mean()
        data = data.dropna()
        
    elif ma_type == "EMA_EMA":
        data['SMA_S'] = data['Close'].ewm(span=sma_s, adjust=False).mean()
        data['SMA_M'] = data['Close'].ewm(span=sma_l, adjust=False).mean()
        data = data.dropna()
        
    return data

def find_up_down(data):
    up_indices = []
    down_indices = []

    for i in range(1, len(data)):
        if data['SMA_S'][i] > data['SMA_M'][i] and data['SMA_S'][i - 1] <= data['SMA_M'][i - 1]:
            up_indices.append(i)

        if data['SMA_S'][i] < data['SMA_M'][i] and data['SMA_S'][i - 1] >= data['SMA_M'][i - 1]:
            down_indices.append(i)

    return up_indices, down_indices

def analyze_segments(data, up_indices, down_indices):
    merged_indices = sorted(up_indices + down_indices)
    
    segment_types = []
    start_indices = []
    end_indices = []
    reference_close_prices = []
    highest_high_prices = []
    lowest_low_prices = []
    segment_dates = []

    for i in range(len(merged_indices)-1):
        start_idx = merged_indices[i]
        end_idx = merged_indices[i + 1]

        if start_idx in up_indices:
            segment_type = "up"
        else:
            segment_type = "down"

        reference_close_price = data['Close'][start_idx]
        highest_high_price = data['High'][start_idx:end_idx].max()
        lowest_low_price = data['Low'][start_idx:end_idx].min()
        segment_date = data.index[start_idx]

        segment_types.append(segment_type)
        start_indices.append(start_idx)
        end_indices.append(end_idx)
        reference_close_prices.append(reference_close_price)
        highest_high_prices.append(highest_high_price)
        lowest_low_prices.append(lowest_low_price)
        segment_dates.append(segment_date)

    df = pd.DataFrame({
        'Segment Type': segment_types,
        'Start Index': start_indices,
        'End Index': end_indices,
        'Reference Close Price': reference_close_prices,
        'Highest High Price': highest_high_prices,
        'Lowest Low Price': lowest_low_prices,
        'Segment Date': segment_dates
    })
    df['% High Price Difference'] = (df['Highest High Price'] - df['Reference Close Price']) / df['Reference Close Price'] * 100
    df['% Low Price Difference'] = (df['Lowest Low Price'] - df['Reference Close Price']) / df['Reference Close Price'] * 100
    df['% up-down Difference'] = df['Reference Close Price'].pct_change() * 100
    df['% up-down Difference'].fillna(0, inplace=True)  # Replace NaN values with 0 for the first row
    df["bars taken"] = df["End Index"] - df["Start Index"] 
    df['% up-down Difference'] = df['% up-down Difference'].shift(-1)
    df['trade_close'] = df['Reference Close Price'].shift(-1)
    df["Returns"] = df["% up-down Difference"]
    df.loc[df['Segment Type'] == 'down', 'Returns'] *= -1
    return df

def calculate_profit_losses(df, trade_type, sma_s, sma_l):
    long_profit_trades = 0
    long_losses_trades = 0
    short_profit_trades = 0
    short_losses_trades = 0
    long_profit = []
    long_loss = []
    short_profit = []
    short_loss = []
    total_trades = 0
    trade_value = 100
    portfolio_value = 0
    portfolio_values = []

    
    for i in range(len(df)):
        if trade_type == "Long":
            
            if df["Segment Type"][i] == "up" and df["Returns"][i] > 0:
                long_profit_trades += 1
                long_profit.append(df["Returns"][i])
                profit = trade_value * abs(df["Returns"][i] / 100) 
                portfolio_value += profit
            
            elif df["Segment Type"][i] == "up" and df["Returns"][i] < 0:
                long_losses_trades += 1
                long_loss.append(df["Returns"][i])
                loss = trade_value * abs(df["Returns"][i] / 100) 
                portfolio_value -= loss
                
            total_trades = (long_profit_trades
                            + long_losses_trades)
                
        elif trade_type == "Short":
            
            if df["Segment Type"][i] == "down" and df["Returns"][i] > 0:
                short_profit_trades += 1
                short_profit.append(df["Returns"][i])
                profit = trade_value * abs(df["Returns"][i] / 100) 
                portfolio_value += profit

            elif df["Segment Type"][i] == "down" and df["Returns"][i] < 0:
                short_losses_trades += 1
                short_loss.append(df["Returns"][i])
                loss = trade_value * abs(df["Returns"][i] / 100) 
                portfolio_value -= loss
                
            total_trades = (short_profit_trades
                            + short_losses_trades)
                
        elif trade_type == "Both":
            
            if df["Segment Type"][i] == "up" and df["Returns"][i] > 0:
                long_profit_trades += 1
                long_profit.append(df["Returns"][i])
                profit = trade_value * abs(df["Returns"][i] / 100) 
                portfolio_value += profit
                portfolio_values.append(portfolio_value)

            elif df["Segment Type"][i] == "up" and df["Returns"][i] < 0:
                long_losses_trades += 1
                long_loss.append(df["Returns"][i])
                loss = trade_value * abs(df["Returns"][i] / 100) 
                portfolio_value -= loss

            if df["Segment Type"][i] == "down" and df["Returns"][i] > 0:
                short_profit_trades += 1
                short_profit.append(df["Returns"][i])
                profit = trade_value * abs(df["Returns"][i] / 100) 
                portfolio_value += profit

            elif df["Segment Type"][i] == "down" and df["Returns"][i] < 0:
                short_losses_trades += 1
                short_loss.append(df["Returns"][i])
                loss = trade_value * abs(df["Returns"][i] / 100) 
                portfolio_value -= loss

            total_trades = (long_profit_trades
                            + long_losses_trades
                            +short_profit_trades
                            + short_losses_trades)
        portfolio_values.append(portfolio_value)


    pnl_summary = pd.DataFrame({
        'sma_s': [sma_s],
        'sma_l': [sma_l],
        'trade_type': [trade_type],
        'long_profit_trades': (long_profit_trades),
        'long_losses_trades': (long_losses_trades),
        'short_profit_trades': (short_profit_trades),
        'short_losses_trades': (short_losses_trades),
        'sum_long_profit': sum(long_profit),
        'sum_long_loss': sum(long_loss),
        'sum_short_profit': sum(short_profit),
        'sum_short_loss': sum(short_loss),
        'total_trades': total_trades,
        "portfolio_value" : portfolio_value
    })
    pnl_portfolio = pd.DataFrame({
        "portfolio_value": portfolio_values
        })
    return pnl_summary, pnl_portfolio
        

# Streamlit app
def sma_cross():
    # st.set_page_config(page_title="Trading Strategy Dashboard", page_icon=":bar_chart:", layout="wide")
    st.title("Moving Average Trading Analysis")
    guide_placeholder = st.empty()

    # Display the User Guide only if it's the first time the app is loaded
    if 'guide_loaded' not in st.session_state:
        # Display the User Guide
        guide_placeholder.markdown("""
        ---

        ## Moving Average Trading Analysis User Guide

        ### Introduction:

        Welcome to the Moving Average Trading Analysis app! This tool helps you analyze historical stock data and implement a trading strategy based on Moving Averages.

        ### Getting Started:

        1. **User Input:**
        - On the left sidebar, you'll find the "User Input" section. Here, you can customize your analysis by providing the following information:
            - **Symbol (e.g., BTC-USD):** Enter the stock symbol you want to analyze (default: "BTC-USD").
            - **Start Date:** Select the start date for historical data.
            - **End Date:** Select the end date for historical data.
            - **SMA Short Window:** Choose the window size for the Short Simple Moving Average (SMA).
            - **SMA Long Window:** Choose the window size for the Long Simple Moving Average (SMA).
            - **Moving Average Combination:** Select the type of Moving Average combination to use (options: EMA_SMA, SMA_EMA, SMA_SMA, EMA_EMA).
            - **Trade Type:** Choose the trading strategy (options: Long, Short, Both).

        2. **Testing the Analysis:**
        - After entering your preferences, click the "Test" button to initiate the analysis.

        ### Results:

        1. **Historical Data:**
        - The initial section displays the historical data for the selected stock.

        2. **Trading Signals:**
        - A chart is displayed showing the closing price of the stock along with the Short and Long Simple Moving Averages.

        3. **Equity Curve:**
        - An equity curve chart is shown, representing the portfolio value over time based on the trading strategy.

        4. **Returns Chart:**
        - A chart illustrating the returns over time based on the trading strategy.

        5. **Trade Summary:**
        - A bar chart providing a summary of the number of profitable and losing trades for both long and short positions, along with the total number of trades.

        6. **Profit and Loss Summary:**
        - A table summarizing the key statistics of the analysis, including the number of profitable and losing trades, total returns, and more.

        ### Interpreting the Results:

        - **Total Returns:**
        - The total returns percentage is displayed at the top, indicating the overall performance of the selected trading strategy.

        - **Trade Summary:**
        - The bar chart gives a visual representation of the number of profitable and losing trades for both long and short positions.

        - **Profit and Loss Summary:**
        - The table provides detailed statistics on the trading strategy, including the number of trades, profits, losses, and total returns.

        ### Exporting Results:

        - **CSV Export:**
        - The app automatically saves a CSV file containing detailed segment analysis results with the filename format: `<symbol>_sma_<sma_s>_<sma_l>_<ma_type>_<start_date>_<end_date>.csv`.

        ### Conclusion:

        Explore the results and use the information to make informed decisions about your trading strategy. Experiment with different parameters to optimize your approach.

        Happy trading!

        ---

        """)

        # Mark that the user guide has been loaded
        st.session_state.guide_loaded = True
    
    st.sidebar.header("User Input")
    max_date = date.today()
    symbol = st.sidebar.text_input("Enter Symbol (e.g., BTC-USD):", value = "BTC-USD")
    default_start_date = datetime.date(2014, 1, 1)
    start_date = st.sidebar.date_input("Start Date", value = default_start_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_value=max_date)
    interval = st.sidebar.selectbox("select time interval", ["5m","15m", "30m", "1h", "1d"])
    sma_s = st.sidebar.slider("Select SMA Short Window", 1, 100, 21)
    sma_l = st.sidebar.slider("Select SMA Long Window", 1, 100, 50)
    ma_type = st.sidebar.selectbox("Select Moving Average Combination", ["EMA_SMA", "SMA_EMA", "SMA_SMA", "EMA_EMA"])
    trade_type = st.sidebar.radio("Select Trade Type", ["Long", "Short", "Both"])
        
    if st.sidebar.button("Test"):
        if interval == "5m" or interval == "15m" or interval == "30m" or interval == "1h":
            st.write(f"You have selected {interval} so the strategy will be tested for 60 days only due to limitation of yfinance library soon we will work towords this to facilitate the feature so you can test the strategy over a desired date range")
            max_date = date.today()
            start_date = (max_date - timedelta(days=59)).strftime('%Y-%m-%d')
            end_date = max_date
            df = get_data(symbol, start_date, end_date, interval)
        else:
            df = get_data(symbol, start_date, end_date, interval)
        st.subheader("Historical Data")
        st.dataframe(df)

        data = calculate_sma(df, sma_s, sma_l, ma_type)
        up_indices, down_indices = find_up_down(data)
        segments_df = analyze_segments(data, up_indices, down_indices)
        segments_df.to_csv(f"{symbol}_sma_{sma_s}_{sma_l}_{ma_type}_{start_date}_{end_date}.csv", index=False)

        # Display results
        st.subheader("Generating Trade signals And Detailed Trade Report")
        st.dataframe(segments_df)
        # total_returns = segments_df["Returns"].sum()
        # st.info(f"Total Returns: {total_returns} %")

        # Calculate profit and losses
        pnl_summary, pnl_portfolio = calculate_profit_losses(segments_df, trade_type, sma_s, sma_l)
        total_returns = pnl_summary["portfolio_value"].iloc[0]
        st.subheader("Strategy_performance")
        st.info(f"Total Returns: {total_returns} %")

        # Calculate profit and losses
        # pnl_summary, pnl_portfolio = calculate_profit_losses(segments_df, trade_type, sma_s, sma_l)
        # st.dataframe(pnl_summary)
        st.subheader("Trade_Stasts")
        st.dataframe(pnl_summary)
        
        # Display results
        st.subheader("Trading_Signals")
        st.line_chart(data[['Close', 'SMA_S', 'SMA_M']])
        
        st.subheader("Equity_Curve")
        st.line_chart(pnl_portfolio['portfolio_value'])
        
        st.subheader("Returns_chart")
        st.line_chart(segments_df['Returns'])
        
        st.subheader("Trade_summary")
        st.bar_chart(pnl_summary[['long_profit_trades', 'short_profit_trades', 'total_trades']])
        st.sidebar.header("Contact Info")
        st.sidebar.write("Email: work.abtech@gmail.com")
        st.sidebar.write("email us for any feedback & suggestions")

    
selected_strategy = st.sidebar.selectbox("✅Choose a strategy", ["MA Cross",
                                                                "MA Cross with TP & SL"
                                                               ])


# Call the selected strategy based on user input
if selected_strategy == "MA Cross":
    sma_cross()
elif selected_strategy == "MA Cross with TP & SL":
    sma_tp_sl()
else:
    print("please select strategy from the sidebar")
