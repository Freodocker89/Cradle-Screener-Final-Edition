import streamlit as st
from streamlit_autorefresh import st_autorefresh
import ccxt
import pandas as pd
import datetime

# Page setup
st.set_page_config(layout="wide")
st.title("📊 Cradle Screener")

# Bitget API
BITGET = ccxt.bitget()
TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w', '1M']

# Select timeframes
selected_timeframes = st.multiselect("Select Timeframes to Scan", TIMEFRAMES, default=['1h', '4h', '1d'])

# Manual refresh button
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []
if 'last_scanned' not in st.session_state:
    st.session_state.last_scanned = None

if st.button("🔄 Refresh Screener"):
    st.success("✅ Screener refreshed!")
    st.session_state.scan_results = []  # Reset results
    st.session_state.last_scanned = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load market list
    markets = BITGET.load_markets()
    symbols = [s for s in markets if '/USDT' in s and 'SPOT' not in markets[s]['id']]

    def is_cradle_setup(df):
        if len(df) < 3:
            return False

        ema10 = df['close'].ewm(span=10).mean()
        ema20 = df['close'].ewm(span=20).mean()
        lower_cradle = ema10.combine(ema20, min)
        upper_cradle = ema10.combine(ema20, max)

        c1 = df.iloc[-3]
        c2 = df.iloc[-2]
        c3 = df.iloc[-1]

        is_bearish = c1['close'] < c1['open']
        is_small_bull = c2['close'] > c2['open']
        breaks_high = c3['high'] > c2['high']
        closed_in_cradle = lower_cradle.iloc[-3] <= c1['close'] <= upper_cradle.iloc[-3]

        return is_bearish and is_small_bull and breaks_high and closed_in_cradle

    for symbol in symbols:
        for tf in selected_timeframes:
            try:
                ohlcv = BITGET.fetch_ohlcv(symbol, tf, limit=50)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)

                if is_cradle_setup(df):
                    st.session_state.scan_results.append({
                        'Symbol': symbol,
                        'Timeframe': tf,
                        'Last Close': df['close'].iloc[-1]
                    })
            except Exception as e:
                st.warning(f"Error fetching {symbol} on {tf}: {e}")

# Show last scanned time
if st.session_state.last_scanned:
    st.caption(f"Last scanned: {st.session_state.last_scanned}")

# Show results
if st.session_state.scan_results:
    df_results = pd.DataFrame(st.session_state.scan_results)
    st.dataframe(df_results)
else:
    st.info("No Cradle setups found yet. Click the 'Refresh Screener' button to begin scanning.")

