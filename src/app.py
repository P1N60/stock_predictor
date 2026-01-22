import streamlit as st
import pandas as pd
import sys
import io
from methods.screener_methods import Stock

# Page config
st.set_page_config(page_title="Stock Screener", layout="wide")

st.title("Stock Screener Analysis")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    symbol_list = st.selectbox(
        "Select Ticker List",
        options=["simple", "danish", "filtered", "all"],
        index=0
    )
    
    run_button = st.button("Run Screener", type="primary")

def load_symbols(list_type):
    base_path = "../data/tickers"
    if list_type == "all":
        try:
            l1 = pd.read_csv(f"{base_path}/tickers.csv")["Ticker"].tolist()
            l2 = pd.read_csv(f"{base_path}/danish_tickers.csv")["Ticker"].tolist()
            l3 = pd.read_csv(f"{base_path}/simple_tickers.csv")["Ticker"].to_list()
            symbols = l1 + l2 + l3
        except Exception as e:
            st.error(f"Error reading sticker files: {e}")
            return []
    elif list_type == "filtered":
        symbols = pd.read_csv(f"{base_path}/screener_filtered_tickers.csv")["Ticker"].tolist()
    elif list_type == "danish":
        symbols = pd.read_csv(f"{base_path}/danish_tickers.csv")["Ticker"].tolist()
    else:
        symbols = pd.read_csv(f"{base_path}/simple_tickers.csv")["Ticker"].tolist()
    return list(set(symbols))

if 'df_results' not in st.session_state:
    st.session_state.df_results = None

if run_button:
    st.write(f"Fetching data for **{symbol_list}** list...")
    
    symbols = load_symbols(symbol_list)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    df = pd.DataFrame()
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"Processing {symbol} ({i+1}/{len(symbols)})...")
        
        # Suppress stderr to avoid clutter (e.g. yfinance errors)
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            stock = Stock(symbol)
            summary = stock.summary()
            df = pd.concat([df, summary])
        except Exception:
            pass
        finally:
            sys.stderr = old_stderr
        
        progress_bar.progress((i + 1) / len(symbols))
        
    status_text.text("Done!")
    
    if not df.empty:
        df = df.sort_values(by="Recommendation Score", ascending=False)
        st.session_state.df_results = df
    else:
        st.warning("No data found or all fetches failed.")

if st.session_state.df_results is not None:
    df = st.session_state.df_results
    st.subheader("Results")
    
    # Styling the dataframe
    st.dataframe(
        df.style.background_gradient(subset=["Recommendation Score"], cmap="RdYlGn"), 
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
