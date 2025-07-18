import requests # type: ignore
import pandas as pd # type: ignore
import time
from plyer import notification # type: ignore
from playsound import playsound # type: ignore
import threading
import logging


#--------------------------------------------------------
# Parameters and API info
#--------------------------------------------------------


# Binance API URL for historical data (Default: BTC/USDT)
SYMBOL = "BTCUSDT"
INTERVAL = "15m"  # 15-minute candles
API_URL = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=500"

# Strategy Parameters
SHORT_MA = 10  # Short moving average period
LONG_MA = 50  # Long moving average period
RSI_PERIOD = 14  # RSI lookback period
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30


#--------------------------------------------------------
# Configure two separate loggers
#--------------------------------------------------------

# Logger for price and indicator data
price_indicator_logger = logging.getLogger("PriceIndicatorLogger")
price_indicator_logger.setLevel(logging.INFO)
price_indicator_file_handler = logging.FileHandler("price_indicator_log.txt")
price_indicator_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
price_indicator_logger.addHandler(price_indicator_file_handler)

# Logger for buy and sell notifications
trade_signal_logger = logging.getLogger("TradeSignalLogger")
trade_signal_logger.setLevel(logging.INFO)
trade_signal_file_handler = logging.FileHandler("trade_signal_log.txt")
trade_signal_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
trade_signal_logger.addHandler(trade_signal_file_handler)


#--------------------------------------------------------
# Algorithm functions and vars 
#--------------------------------------------------------


# Get price data from binance
def get_price_data():
    """Fetch historical price data from Binance API"""
    response = requests.get(API_URL)
    data = response.json()
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset", "trades", "taker_base", "taker_quote", "ignore"])
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)
    price_indicator_logger.info("Fetched price data from Binance API.")
    return df

# Calculate values for indicators
def calculate_indicators(df):
    """Calculate Moving Averages and RSI"""
    df["SMA"] = df["close"].rolling(SHORT_MA).mean()
    df["LMA"] = df["close"].rolling(LONG_MA).mean()

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(RSI_PERIOD).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    price_indicator_logger.info("Calculated indicators (SMA, LMA, RSI).")
    return df

# Check buy or sell signals
def check_trade_signals(df):
    """Check for buy/sell signals based on MA crossover and RSI"""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    buy_signal = (
        prev["SMA"] < prev["LMA"] and latest["SMA"] > latest["LMA"] and latest["RSI"] < RSI_OVERBOUGHT  
    )
    sell_signal = (
        prev["SMA"] > prev["LMA"] and latest["SMA"] < latest["LMA"] and latest["RSI"] > RSI_OVERSOLD  
    )
    
    return buy_signal, sell_signal

# Log and notify/send signal
def send_notification(message):
    """Send a desktop notification"""
    sound_thread = threading.Thread(target=playsound, args=("notification.mp3",))  # Replace with your sound file
    sound_thread.start()

    notification.notify(
        title="Crypto Trading Signal",
        message=message,
        timeout=5
    )
    trade_signal_logger.info(f"Notification sent: {message}")


#--------------------------------------------------------
# Trade Signal Management
#--------------------------------------------------------


last_trade = None 

def manage_trade_signals(buy_signal, sell_signal, latest_price): 
    """Ensure buy and sell signals are only sent in alternating order"""
    global last_trade 
    
    if buy_signal and last_trade != "BUY":
        
        send_notification(f"BUY SIGNAL for {SYMBOL} at ${latest_price:.2f}")
        
        trade_signal_logger.info(f"BUY SIGNAL for {SYMBOL} at ${latest_price:.2f}")
        
        print(f"BUY SIGNAL for {SYMBOL} at ${latest_price:.2f}")
        print(" ")
        
        last_trade = "BUY"

    elif sell_signal and last_trade != "SELL":
        
        send_notification(f"SELL SIGNAL for {SYMBOL} at ${latest_price:.2f}")
        
        trade_signal_logger.info(f"SELL SIGNAL for {SYMBOL} at ${latest_price:.2f}")
        
        print(f"SELL SIGNAL for {SYMBOL} at ${latest_price:.2f}")
        print(" ")
        
        last_trade = "SELL"


#--------------------------------------------------------
# Main
#--------------------------------------------------------


def main():
    while True:
        df = get_price_data()
        df = calculate_indicators(df)
        buy_signal, sell_signal = check_trade_signals(df)
        
        latest_price = df.iloc[-1]['close']
        latest_sma = df.iloc[-1]['SMA']
        latest_lma = df.iloc[-1]['LMA']
        latest_rsi = df.iloc[-1]['RSI']

        # Log the current data
        price_indicator_logger.info(f"Current {SYMBOL} Price: ${latest_price:.2f}")
        price_indicator_logger.info(f"SMA ({SHORT_MA}): ${latest_sma:.2f}, LMA ({LONG_MA}): ${latest_lma:.2f}, RSI ({RSI_PERIOD}): {latest_rsi:.2f}")
        price_indicator_logger.info(" ")
        price_indicator_logger.info(" ")
        price_indicator_logger.info(" ")

        print(f"Current {SYMBOL} Price: ${latest_price:.2f}")
        print(f"SMA ({SHORT_MA}): ${latest_sma:.2f}, LMA ({LONG_MA}): ${latest_lma:.2f}, RSI ({RSI_PERIOD}): {latest_rsi:.2f}")
        print(" ")
        
        manage_trade_signals(buy_signal, sell_signal, latest_price)

        time.sleep(1.5)  # Run every 1.5 seconds

if __name__ == "__main__":
    main()
