import pandas as pd
import re
import yfinance as yf
import time

# --- PART 1: CLEANING THE DATA (Extract & Transform) ---
print("Step 1: Reading and Cleaning Data...")

file_path = 'LoC14.csv' # Make sure your file is named this!

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

data = []
current_tier = None
# This regex looks for 1-5 capital letters at the start of a line (The Ticker)
ticker_pattern = re.compile(r'^([A-Z]{1,5}),')

for line in lines:
    line = line.strip()
    
    # Identify the "Tiers" (The Labels)
    if "TIER" in line and "source" in line:
        if "TIER 1" in line: current_tier = "Tier 1: True Allies"
        elif "TIER 2" in line: current_tier = "Tier 2: Battle Tested"
        elif "TIER 3" in line: current_tier = "Tier 3: Folded/Neutral"
        elif "TIER 4" in line: current_tier = "Tier 4: The Enemy"
        continue

    # Skip garbage lines
    if "Ticker,Company" in line or line.startswith("Proven Receipts") or line == ",,":
        continue

    # Extract Company Data
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
        # If a line has no ticker, it's a continuation of the previous reason
        data[-1]['Reason'] += " " + line

df = pd.DataFrame(data)

# Clean up the text (Remove tags)
df['Reason'] = df['Reason'].str.replace(r'\', ', regex=True).str.strip()

# Extract Money (The "Quantifier" part)
def extract_money(text):
    # Finds $120M, $1B, etc.
    match = re.search(r'\$(\d+(?:\.\d+)?)\s*(M|B|Million|Billion)', text, re.IGNORECASE)
    if match:
        amount = float(match.group(1))
        unit = match.group(2).upper()
        if 'B' in unit: return amount * 1_000_000_000
        if 'M' in unit: return amount * 1_000_000
    return 0

df['Committed_Capital'] = df['Reason'].apply(extract_money)

print(f"Data Cleaned! Found {len(df)} companies.")

# --- PART 2: THE ENRICHMENT (Adding Yahoo Finance Data) ---
print("Step 2: Enriching with Market Data (This may take 2-3 minutes)...")

tickers = df['Ticker'].tolist()
sectors = []
industries = []
current_prices = []
market_caps = []

# We loop through tickers to get live data
# (Batching is faster, but looping is safer for error handling on small lists)
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        # Fast info fetch
        info = stock.fast_info 
        
        # Sometimes fast_info doesn't have sector, so we check standard info if needed
        # But for speed, we will try to stick to basics or handle missing data gracefully
        
        # Note: yfinance can be tricky. We will try to get metadata.
        # If fast_info fails, we might need stock.info (slower)
        
        # Let's use stock.info for sector/industry (slower but accurate)
        meta = stock.info
        
        sectors.append(meta.get('sector', 'Unknown'))
        industries.append(meta.get('industry', 'Unknown'))
        current_prices.append(meta.get('currentPrice', 0))
        market_caps.append(meta.get('marketCap', 0))
        
        print(f"Fetched: {ticker}")
    except Exception as e:
        print(f"Could not fetch {ticker}: {e}")
        sectors.append('Unknown')
        industries.append('Unknown')
        current_prices.append(0)
        market_caps.append(0)

# Add new columns to our DataFrame
df['Sector'] = sectors
df['Industry'] = industries
df['Stock_Price'] = current_prices
df['Market_Cap'] = market_caps

# --- PART 3: SAVE THE FINAL FILE ---
output_filename = 'Final_Project_Data.csv'
df.to_csv(output_filename, index=False)
print(f"SUCCESS! File saved as {output_filename}. Ready for Power BI.")