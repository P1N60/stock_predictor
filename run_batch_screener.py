#!/usr/bin/env python3
"""
Batch stock screener runner without browser/Streamlit.
Handles snapshot comparison and Discord notification logic.
"""
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, "src"))

from methods.screener_methods import Stock, BUY_THRESHOLD

# Configuration
CACHE_DIR = Path.home() / ".openclaw" / "workspace" / ".cache" / "screener"
CURRENT_SNAPSHOT = CACHE_DIR / "current.csv"
PREVIOUS_SNAPSHOT = CACHE_DIR / "previous.csv"
OWNED_THRESHOLD = 0.5  # Same as BUY_THRESHOLD
MIN_SCORE_CHANGE = 0.5

def ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_symbols(list_type="Most interesting (Default)"):
    """Load ticker symbols from specified list."""
    base_path = os.path.join(current_dir, "data", "tickers")
    
    if list_type == "All":
        symbols = pd.read_csv(os.path.join(base_path, "screener_filtered_tickers.csv"))["Ticker"].tolist()
    elif list_type == "European":
        european_symbols = pd.read_csv(os.path.join(base_path, "european_tickers.csv"))["Ticker"].tolist()
        danish_symbols = pd.read_csv(os.path.join(base_path, "danish_tickers.csv"))["Ticker"].tolist()
        symbols = european_symbols + danish_symbols
    elif list_type == "Danish":
        symbols = pd.read_csv(os.path.join(base_path, "danish_tickers.csv"))["Ticker"].tolist()
    else:  # Most interesting (Default)
        symbols = pd.read_csv(os.path.join(base_path, "simple_tickers.csv"))["Ticker"].tolist()
    
    return list(set(symbols))

def fetch_stock_data(symbol):
    """Fetch stock data and return summary row."""
    try:
        return Stock(symbol).summary()
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}", file=sys.stderr)
        return None

def run_screener(list_type="Most interesting (Default)"):
    """Run the screener and return results DataFrame."""
    symbols = load_symbols(list_type)
    print(f"[INFO] Running screener for {len(symbols)} symbols from '{list_type}'...", file=sys.stderr)
    
    df = pd.DataFrame()
    
    for i, symbol in enumerate(symbols):
        print(f"[PROGRESS] {i+1}/{len(symbols)}: {symbol}", file=sys.stderr)
        
        try:
            summary = fetch_stock_data(symbol)
            if summary is not None:
                df = pd.concat([df, summary], ignore_index=True)
        except Exception as e:
            print(f"[ERROR] Failed to process {symbol}: {e}", file=sys.stderr)
            continue
    
    if not df.empty:
        df = df.sort_values(by="Final Score", ascending=False).reset_index(drop=True)
    
    return df

def load_previous_snapshot():
    """Load previous snapshot if it exists."""
    if PREVIOUS_SNAPSHOT.exists():
        try:
            return pd.read_csv(PREVIOUS_SNAPSHOT)
        except Exception as e:
            print(f"[WARN] Could not load previous snapshot: {e}", file=sys.stderr)
    return None

def detect_changes(current_df, previous_df):
    """
    Detect significant changes between current and previous snapshots.
    
    Rules:
    1. Owned=True: Always monitored. Signal changes, buy-zone entry/exit, |Score delta| >= 0.5
    2. Owned=False: Only if entering buy-zone (Signal becomes Buy or Final Score crosses BUY_THRESHOLD)
    3. Ignore earnings entirely
    
    Returns list of change descriptions.
    """
    changes = []
    
    if previous_df is None or previous_df.empty:
        return changes  # First run, no comparison
    
    # Build lookup dictionaries
    prev_dict = {row["Ticker"]: row for _, row in previous_df.iterrows()}
    curr_dict = {row["Ticker"]: row for _, row in current_df.iterrows()}
    
    # Check existing tickers
    for ticker, curr_row in curr_dict.items():
        if ticker not in prev_dict:
            continue  # New ticker, not a change
        
        prev_row = prev_dict[ticker]
        is_owned = curr_row["Owned"]
        
        prev_score = prev_row["Final Score"]
        curr_score = curr_row["Final Score"]
        prev_signal = prev_row["Signal"]
        curr_signal = curr_row["Signal"]
        
        # Check for significant changes
        if is_owned:
            # Rule 1: Owned stocks always monitored
            # Signal change
            if prev_signal != curr_signal:
                changes.append(f"🔄 {ticker}: {prev_signal} → {curr_signal} (score {prev_score:.2f} → {curr_score:.2f})")
            # Score delta >= 0.5
            elif abs(curr_score - prev_score) >= MIN_SCORE_CHANGE:
                changes.append(f"📊 {ticker}: Score {prev_score:.2f} → {curr_score:.2f}")
        else:
            # Rule 2: Unowned stocks only if entering buy-zone
            prev_in_buy = prev_signal == "Buy" or prev_score >= BUY_THRESHOLD
            curr_in_buy = curr_signal == "Buy" or curr_score >= BUY_THRESHOLD
            
            if not prev_in_buy and curr_in_buy:
                changes.append(f"🚀 {ticker}: Entering buy-zone (score {curr_score:.2f})")
    
    return changes

def main():
    ensure_cache_dir()
    
    # Rotate snapshots: current -> previous
    if CURRENT_SNAPSHOT.exists():
        CURRENT_SNAPSHOT.rename(PREVIOUS_SNAPSHOT)
        print(f"[INFO] Rotated snapshot: current → previous", file=sys.stderr)
    
    # Load previous for comparison
    previous_df = load_previous_snapshot()
    
    # Run screener
    current_df = run_screener("Most interesting (Default)")
    
    if current_df.empty:
        print("[ERROR] Screener returned no results", file=sys.stderr)
        sys.exit(1)
    
    # Save current snapshot
    current_df.to_csv(CURRENT_SNAPSHOT, index=False)
    print(f"[INFO] Saved current snapshot to {CURRENT_SNAPSHOT}", file=sys.stderr)
    
    # Detect changes
    changes = detect_changes(current_df, previous_df)
    
    # Output result
    if previous_df is None or previous_df.empty:
        # First run: baseline established, no Discord message
        print("NO_REPLY", file=sys.stdout)
        print("[INFO] First run: baseline established. No Discord notification.", file=sys.stderr)
    elif changes:
        # Changes detected: send Discord message
        message = f"<@326383878157631516>\n"
        # Include top 6 lines of changes
        for change in changes[:6]:
            message += f"{change}\n"
        print(message, file=sys.stdout)
        print(f"[INFO] {len(changes)} significant change(s) detected. Sending Discord message.", file=sys.stderr)
    else:
        # No changes
        print("NO_REPLY", file=sys.stdout)
        print("[INFO] No significant changes detected.", file=sys.stderr)

if __name__ == "__main__":
    main()
