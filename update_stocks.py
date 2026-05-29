import json
import os
import sys
from datetime import datetime
import yfinance as yf
import pandas as pd
import requests

def load_tickers_from_file(filename, default_list):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(";".join(default_list))
        return default_list
    with open(filename, "r") as f:
        content = f.read().strip()
    return [symbol.strip().upper() for symbol in content.split(";") if symbol.strip()]

def calculate_local_technical_indicators(df):
    """Calculates fallback mathematical RSI-14 and MACD metrics if API limits hit"""
    if len(df) < 30:
        return 50.0, "Neutral Phase"
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    current_rsi = float(rsi.iloc[-1])
    
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    
    macd_val = macd_line.iloc[-1]
    sig_val = signal_line.iloc[-1]
    macd_str = "Bullish Crossover" if macd_val > sig_val else "Bearish Phase"
    
    return current_rsi, macd_str

def fetch_twelve_data_metrics(symbol, api_key):
    """Fetches high-accuracy indicators directly from Twelve Data API"""
    if not api_key:
        return None, None
    try:
        url = f"https://api.twelvedata.com/rsi?symbol={symbol}&interval=1day&outputsize=1&apikey={api_key}"
        res = requests.get(url, timeout=10).json()
        if "values" in res and len(res["values"]) > 0:
            rsi = float(res["values"][0]["rsi"])
            return rsi, "Verified Feed"
    except Exception:
        pass
    return None, None

def main():
    print("Executing Institutional Analytics Engine Update...")
    
    # Retrieve Twelve Data key securely from OS Environment instead of hardcoding
    twelve_key = os.getenv("TWELVEDATA_API_KEY")
    
    list1_tickers = load_tickers_from_file("Stock_List.txt", ["SOFI", "RKLB", "OKLO"])
    list2_tickers = load_tickers_from_file("Stock_List2.txt", ["NVDA", "INTC", "AAPL"])
    all_tickers = list(set(list1_tickers + list2_tickers))
    
    global_registry = {}

    for symbol in all_tickers:
        print(f" Processing Core Diagnostics: {symbol}")
        try:
            # 1. Gather historical baseline via yfinance
            ticker_obj = yf.Ticker(symbol)
            df = ticker_obj.history(period="3mo")
            
            if df.empty:
                print(f"   ⚠️ No trading matrix found for {symbol}")
                continue
                
            current_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            pct_change = ((current_price - prev_close) / prev_close) * 100
            trailing_history = df['Close'].tail(7).tolist()
            
            # 2. Extract technical signatures (Combines Twelve Data & Local computing models)
            td_rsi, td_status = fetch_twelve_data_metrics(symbol, twelve_key)
            local_rsi, local_macd = calculate_local_technical_indicators(df)
            
            final_rsi = td_rsi if td_rsi is not None else local_rsi
            macd_signature = "TwelveData Direct" if td_status else local_macd
            
            global_registry[symbol] = {
                "sym": symbol,
                "price": current_price,
                "change": pct_change,
                "rsi": final_rsi,
                "macdStr": macd_signature,
                "history": trailing_history
            }
            print(f"   ✅ Metrics Synced: RSI {final_rsi:.1f} | Strategy: {macd_signature}")
        except Exception as e:
            print(f"   ⚠️ Skipping {symbol}: Processing boundary exception ({e})")

    sync_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    output_data = {
        "sync_timestamp": sync_time,
        "list1_symbols": list1_tickers,
        "list2_symbols": list2_tickers,
        "registry": global_registry
    }
    
    with open("./live_market.json", "w") as f:
        json.dump(output_data, f, indent=2)
    print("Market Data Packet compilation completed successfully.")

if __name__ == "__main__":
    main()