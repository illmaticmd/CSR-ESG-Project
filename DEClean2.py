import pandas as pd
import re
import yfinance as yf
import os
import time

# --- PART 1: CLEANING THE DATA ---
print("Step 1: Reading and Cleaning Data...")

# Get the folder where this script is currently living
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'LoC14.csv')

print(f"Looking for file at: {file_path}")

if not os.path.exists(file_path):
    print("ERROR: File not found!")
    print(f"Please ensure the file is named 'LoC14.csv' and is in: {script_dir}")
    exit()

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

data = []
current_tier = None
ticker_pattern = re.compile(r'^([A-Z]{1,5}),')

for line in lines:
    line = line.strip()
    
    # Identify Tiers
    if "TIER" in line and "source" in line:
        if "TIER 1" in line: current_tier = "Tier 1: True Allies"
        elif "TIER 2" in line: current_tier = "Tier 2: Battle Tested"
        elif "TIER 3" in line: current_tier = "Tier 3: Folded/Neutral"
        elif "TIER 4" in line: current_tier = "Tier 4: The Enemy"
        continue

    # Skip garbage lines
    if "Ticker,Company" in line or line.startswith("Proven Receipts") or line == ",,":
        continue

    match = ticker_pattern.match(line)
    if match:
        parts = line.split(',', 2) 
        if len(parts) >= 3:
            data.append({
                'Tier': current_tier,
                'Ticker': parts[0],
                'Company': parts[1],
                'Reason': parts[2]
            })
    elif line and data:
        # Continuation of previous line
        data[-1]['Reason'] += " " + line

df = pd.DataFrame(data)

# --- THE FIX IS HERE ---
# This regex removes text like ""
# We use r'' to handle backslashes safely
df['Reason'] = df['Reason'].str.replace(r'', '', regex=True).str.strip()

# Extract Money
def extract_money(text):
    match = re.search(r'\$(\d+(?:\.\d+)?)\s*(M|B|Million|Billion)', text, re.IGNORECASE)
    if match:
        amount = float(match.group(1))
        unit = match.group(2).upper()
        if 'B' in unit: return amount * 1_000_000_000
        if 'M' in unit: return amount * 1_000_000
    return 0

df['Committed_Capital'] = df['Reason'].apply(extract_money)

print(f"Data Cleaned! Found {len(df)} companies.")

# --- PART 2: ENRICHMENT (Yahoo Finance) ---
print("Step 2: Enriching with Market Data (This may take 2-3 minutes)...")

tickers = df['Ticker'].tolist()
sectors = []
industries = []
current_prices = []
market_caps = []

# Loop through tickers
for ticker in tickers:
    try:
        # Check if ticker is valid string
        if not isinstance(ticker, str) or len(ticker) < 1:
            raise ValueError("Invalid Ticker")

        # Create Ticker object
        stock = yf.Ticker(ticker)
        
        # We use .info to get sector/industry. 
        # Note: If you get errors here, it's usually network related or bad ticker
        meta = stock.info
        
        sectors.append(meta.get('sector', 'Unknown'))
        industries.append(meta.get('industry', 'Unknown'))
        current_prices.append(meta.get('currentPrice', 0))
        market_caps.append(meta.get('marketCap', 0))
        
        print(f"Fetched: {ticker}")
        
    except Exception as e:
        # If fetch fails, fill with dummy data so script doesn't crash
        print(f"Could not fetch {ticker}: {e}")
        sectors.append('Unknown')
        industries.append('Unknown')
        current_prices.append(0)
        market_caps.append(0)

# Assign lists to DataFrame columns
df['Sector'] = sectors
df['Industry'] = industries
df['Stock_Price'] = current_prices
df['Market_Cap'] = market_caps

# --- PART 3: SAVE ---
output_filename = os.path.join(script_dir, 'Clean_Enriched_Project_Data.csv')
df.to_csv(output_filename, index=False)
print(f"SUCCESS! File saved as: {output_filename}")