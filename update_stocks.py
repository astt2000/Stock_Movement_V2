import json
import os
import sys
from datetime import datetime
import yfinance as yf
import pandas as pd

def load_tickers_from_file(filename, default_list):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(";".join(default_list))
        return default_list
    with open(filename, "r") as f:
        content = f.read().strip()
    return [symbol.strip().upper() for symbol in content.split(";") if symbol.strip()]

def calculate_technical_indicators(df):
    """Calculates high-precision mathematical RSI-14 and MACD parameters"""
    if len(df) < 30:
        return 50.0, "Neutral Phase", "HOLD", 50.0
    
    # 1. True RSI-14 Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    current_rsi = float(rsi.iloc[-1])
    
    # 2. True MACD Calculation (12, 26, 9 parameter standard)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    
    macd_val = macd_line.iloc[-1]
    sig_val = signal_line.iloc[-1]
    macd_str = "Bullish Crossover" if macd_val > sig_val else "Bearish Phase"
    
    # 3. Dynamic Technical Signal Decision Engine
    signal = "HOLD"
    confidence = 50.0
    
    if current_rsi < 30 and macd_val > sig_val:
        signal = "BUY"
        confidence = min(85.0 + (30 - current_rsi), 98.0)
    elif current_rsi < 40 and macd_val > sig_val:
        signal = "BUY"
        confidence = 70.0 + (40 - current_rsi) * 1.5
    elif current_rsi > 70 and macd_val < sig_val:
        signal = "SELL"
        confidence = min(85.0 + (current_rsi - 70), 98.0)
    elif current_rsi > 60 and macd_val < sig_val:
        signal = "SELL"
        confidence = 70.0 + (current_rsi - 60) * 1.5
    else:
        signal = "HOLD"
        confidence = 50.0 + abs(macd_val - sig_val) * 10
        if confidence > 69.0: confidence = 65.0

    return current_rsi, macd_str, signal, min(confidence, 95.0)

def main():
    print("Executing Institutional Analytics Engine Update...")
    list1_tickers = load_tickers_from_file("Stock_List.txt", ["SOFI", "RKLB", "OKLO"])
    list2_tickers = load_tickers_from_file("Stock_List2.txt", ["NVDA", "INTC", "AAPL"])
    all_tickers = list(set(list1_tickers + list2_tickers))
    
    global_registry = {}

    for symbol in all_tickers:
        print(f" Processing Core Diagnostics: {symbol}")
        try:
            ticker_obj = yf.Ticker(symbol)
            info = ticker_obj.info
            full_name = info.get('longName', f"{symbol} Inc.")
            
            df = ticker_obj.history(period="3mo")
            if df.empty:
                continue
                
            current_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            pct_change = ((current_price - prev_close) / prev_close) * 100
            
            h3 = df['Close'].tail(3).tolist()
            trend = "UP" if h3[-1] >= h3[0] else "DOWN"
            
            rsi_val, macd_str, action_signal, conf_level = calculate_technical_indicators(df)
            
            global_registry[symbol] = {
                "sym": symbol,
                "name": full_name,
                "price": current_price,
                "change": pct_change,
                "trend": trend,
                "rsi": rsi_val,
                "macdStr": macd_str,
                "signal": action_signal,
                "confidence": conf_level
            }
            print(f"   ✅ Synchronized: {symbol} ({full_name})")
        except Exception as e:
            print(f"   ⚠️ Skipping {symbol}: {e}")

    sync_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    output_data = {
        "sync_timestamp": sync_time,
        "list1_symbols": list1_tickers,
        "list2_symbols": list2_tickers,
        "registry": global_registry
    }
    
    with open("./live_market.json", "w") as f:
        json.dump(output_data, f, indent=2)

if __name__ == "__main__":
    main()