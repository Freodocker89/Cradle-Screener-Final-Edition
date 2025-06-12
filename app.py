import streamlit as st
import ccxt
import pandas as pd
import datetime

# Set layout to wide
st.set_page_config(layout="wide")

# Setup Bitget API
BITGET = ccxt.bitget()
TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w', '1M']

# Title
st.title("📊 Cradle Screener")

# Timeframe selector
selected_timeframes = st.multiselect("Select Timeframes to Scan", TIMEFRAMES, default=['1h', '4h', '1d'])

# Manual refresh button
refresh = st.button("🔄 Refresh Screener")

# Stop execution unless user clicks refresh
if not refresh:
    st.info("Click the 'Refresh Screener' button to scan for valid Cradle setups.")
    st.stop()

# Continue if refresh button was clicked
st.success("✅ Screener is scanning...")

# Load markets
markets = BITGET.load_markets()
symbols = [s for s in markets if '/USDT' in s and 'SPOT' not in markets[s]['id']]

# Results container
results = []

# Define Cradle check function
def is_cradle_setup(df):
    if len(df) < 3:
        return False

    ema10 = df['close'].ewm(span=10).mean()
    ema20 = df['close'].ewm(span=20).mean()

    lower_cradle = ema10.combine(ema20, min)
    upper_cradle = ema10.combine(ema20, max)

    # Candle -2 is bearish
    c1 = df.iloc[-3]
    c2 = df.iloc[-2]
    c3 = df.iloc[-1]

    # Check candle pattern: bear → small bull → break
    is_bearish = c1['close'] < c1['open']
    is_small_bull = c2['close'] > c2['open'] and (c2['close'] - c2['open']) < (c1['open'] - c1['close']) * 0.5
    breaks_high = c3['high'] > c2['high']

    # In cradle zone?
    closed_in_cradle = (c1['close'] >= lower_cradle.iloc[-3]) and (c1['close'] <= upper_cradle.iloc[-3])

    return is_bearish and is_small_bull and breaks_high and closed_in_cradle

# Loop through symbols and timeframes
for symbol in symbols:
    for tf in selected_timeframes:
        try:
            ohlcv = BITGET.fetch_ohlcv(symbol, tf, limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            if is_cradle_setup(df):
                results.append({
                    'Symbol': symbol,
                    'Timeframe': tf,
                    'Entry Candle Close': df['close'].iloc[-1]
                })

        except Exception as e:
            st.write(f"Error fetching {symbol} ({tf}): {e}")

# Show results
if results:
    df_results = pd.DataFrame(results)
    st.dataframe(df_results)
else:
    st.warning("No valid Cradle setups found.")

