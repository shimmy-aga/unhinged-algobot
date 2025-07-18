import json
import time
import urllib.request

def fetch_binance_data(symbol, interval, limit=10000):
    """Fetch historical data from Binance API."""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return [(float(candle[1]), float(candle[4])) for candle in data]  # (open, close) prices
    except Exception as e:
        print("Error fetching data:", e)
        return []

def simple_moving_average(prices, period):
    """Calculate simple moving average."""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def exponential_moving_average(prices, period):
    """Calculate exponential moving average (EMA)."""
    if len(prices) < period:
        return None
    
    ema = prices[0]  # Start with the first price as the initial EMA
    multiplier = 2 / (period + 1)
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def backtest(data, short_window=15, long_window=55, initial_balance=10000, leverage=1):
    """Backtest a simple moving average crossover strategy with long and short positions."""
    position = 0
    balance = initial_balance  # Initial balance (for example)
    
    for i in range(long_window, len(data)):
        close_prices = [c[1] for c in data[:i]]
        short_ma = exponential_moving_average(close_prices, short_window)
        long_ma = exponential_moving_average(close_prices, long_window)
        
        if short_ma is None or long_ma is None:
            continue
        
        # Buy signal (short MA > long MA)
        if short_ma > long_ma and position <= 0:
            if position < 0:  # Closing short position
                exit_price = data[i][1]
                profit = (entry_price - exit_price) * abs(position)
                balance = (entry_price * abs(position)) + profit  # Add profit to balance
                position = 0
                
                print(" ")
                print(f"CLOSE SHORT at {exit_price}, Profit: {profit:.2f}")
                print(f"BALANCE is {balance}")
            
            # Open long position
            entry_price = data[i][1]
            position = (balance * leverage) / entry_price
            balance = 0  # All funds are used in the position

            print(" ")
            print(f"BUY at {entry_price}")
            print(f"BALANCE is {balance}")
        
        # Sell/Short signal (short MA < long MA)
        elif short_ma < long_ma and position >= 0:
            if position > 0:  # Closing long position
                exit_price = data[i][1]
                profit = (exit_price - entry_price) * abs(position)
                balance = (entry_price * abs(position)) + profit  # Add profit to balance
                position = 0
                
                print(" ")
                print(f"SELL at {exit_price}, Profit: {profit:.2f}")
                print(f"BALANCE is {balance}")
            
            # Open short position
            entry_price = data[i][1]
            position = -(balance * leverage) / entry_price
            balance = balance - abs(position) * entry_price 

            print(" ")
            print(f"SHORT at {entry_price}")
            print(f"BALANCE is {balance}")
    
    # Final position handling
    if position > 0:
        exit_price = data[i][1]
        balance = position * data[-1][1]  # Closing long position
        profit = (exit_price - entry_price) * abs(position)
        balance = (entry_price * abs(position)) + profit
        print(" ")
        print(f"SELL LONG at {data[-1][1]}, Profit: {profit:.2f}")
    elif position < 0:
        exit_price = data[-1][1]
        profit = (entry_price - exit_price) * abs(position)
        balance = (entry_price * abs(position)) + profit  # Closing short position
        print(" ")
        print(f"CLOSE SHORT at {exit_price}, Profit: {profit:.2f}")
    
    return balance

if __name__ == "__main__":
    symbol = "BTCUSDT"
    interval = "15m"
    data = fetch_binance_data(symbol, interval, 10000)
    
    if data:
        final_balance = backtest(data, leverage=1)
        print(f"FINAL BALANCE: ${final_balance:.2f}")
        print(f"--------------------------------------------------------------")
    else:
        print("No data available.")
