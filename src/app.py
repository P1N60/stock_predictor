import streamlit as st # type: ignore
import pandas as pd
import sys
import io
import time
from methods.screener_methods import Stock

# Page config
st.set_page_config(
    page_title="Stock Screener", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("Stock Screener")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    debug = st.checkbox("Debug Mode", value=False)
    sb_symbol_list = st.selectbox(
        "Select Ticker List",
        options=["Most interesting", "Danish", "Filtered"],
        index=0
    )
    sb_run_button = st.button("Run Model", type="primary")

# Logic to handle run triggers
should_run = False
symbol_list = sb_symbol_list

if sb_run_button:
    should_run = True

import os

def load_symbols(list_type):
    # Construct absolute path to data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(current_dir, "..", "data", "tickers")
    
    if list_type == "Filtered":
        symbols = pd.read_csv(os.path.join(base_path, "screener_filtered_tickers.csv"))["Ticker"].tolist()
    elif list_type == "Danish":
        symbols = pd.read_csv(os.path.join(base_path, "danish_tickers.csv"))["Ticker"].tolist()
    else:
        symbols = pd.read_csv(os.path.join(base_path, "simple_tickers.csv"))["Ticker"].tolist()
    return list(set(symbols))

def fetch_stock_data(symbol):
    """
    Fetches stock data.
    """
    return Stock(symbol).summary()

if 'df_results' not in st.session_state:
    st.session_state.df_results = None

if should_run:
    st.write(f"Fetching data for **{symbol_list}** list...")
    
    symbols = load_symbols(symbol_list)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    df = pd.DataFrame()
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"Processing {symbol} ({i+1}/{len(symbols)})...")
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            # Use the cached function
            summary = fetch_stock_data(symbol)
            df = pd.concat([df, summary])
            
            # Politeness buffer
            time.sleep(0.5) 
        except Exception as e:
            # If we get blocked (Too Many Requests), wait it out
            if "429" in str(e) or "Too Many Requests" in str(e):
                status_text.text(f"Rate limited on {symbol}. Cooling down for 1s...")
                time.sleep(1)
                # Optional: try one more time?
                try:
                    summary = fetch_stock_data(symbol)
                    df = pd.concat([df, summary])
                except:
                    pass
            else:
                if debug:
                    st.error(f"Error processing {symbol}: {e}")
        finally:
            sys.stderr = old_stderr
        
        progress_bar.progress((i + 1) / len(symbols))
        
    status_text.text("Done!")
    
    if not df.empty:
        df = df.sort_values(by="Recommendation Score", ascending=False).reset_index(drop=True)
        st.session_state.df_results = df
    else:
        st.warning("No data found or all fetches failed.")

if st.session_state.df_results is not None:
    df = st.session_state.df_results
    st.subheader("Results")

    # Search bar
    search_term = st.text_input("Search (Ticker, Name, or other columns)", "")
    if search_term:
        df = df[
            df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        ]
    
    # Styling the dataframe
    def get_signal_color(val):
        color = '#ffc107' # Hold (Yellow)
        if val == 'Buy':
            color = '#28a745'
        elif val == 'Sell': 
            color = '#dc3545'
        return f'color: {color}; font-weight: bold'

    def get_score_color(row):
        # Determine color based on the Signal column in the same row
        signal = row['Signal']
        color = '#ffc107'
        if signal == 'Buy':
            color = '#28a745'
        elif signal == 'Sell':
            color = '#dc3545'
        # Apply color only to the Recommendation Score column
        return [f'color: {color}; font-weight: bold' if col == 'Recommendation Score' else '' for col in row.index]

    st.dataframe(
        df.style
        .format(precision=2)
        .map(get_signal_color, subset=["Signal"])
        .apply(get_score_color, axis=1),
        use_container_width=True
    )
    
    # Download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name=f"{symbol_list}_screener_results.csv",
        mime="text/csv",
    )
    
    # Detail View section
    st.divider()
    st.header("Stock Details")
    
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_ticker = st.selectbox("Select a Ticker for detailed view", df["Ticker"].unique())
    
    if selected_ticker:
        with st.spinner(f"Loading details for {selected_ticker}..."):
            try:
                # We re-fetch or reuse if we could store objects, 
                # but storing objects in session state might use too much memory.
                # Re-fetching is safer for a fresh view.
                stock_detail = Stock(selected_ticker)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Name", stock_detail.name)
                with col2:
                    st.metric("Symbol", stock_detail.symbol)
                with col3:
                    st.metric("Score", round(stock_detail.recommendation_score(), 2))
                with col4:
                     st.metric("Signal", stock_detail.recommendation_signal())

                st.subheader("Price History (YTD)")
                hist = stock_detail.price_history("ytd")
                st.line_chart(hist)
                
                st.subheader("Full Data")
                st.json(stock_detail.summary().to_dict(orient="records")[0])
                
            except Exception as e:
                st.error(f"Could not load details for {selected_ticker}: {e}")
