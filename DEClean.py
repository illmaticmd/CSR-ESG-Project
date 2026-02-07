import pandas as pd
import re

# Load your file (assuming it's a CSV based on the upload)
file_path = 'LoC14.xlsx'

# We read it as a list of strings first because the structure is irregular
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

data = []
current_tier = None

# Regex to find Tickers (2-5 uppercase letters at start of line)
ticker_pattern = re.compile(r'^([A-Z]{1,5}),')

for line in lines:
    line = line.strip()
    
    # 1. Detect Tier Headers
    if "TIER" in line and "source" in line:
        # Extract "TIER 1", "TIER 2", etc.
        if "TIER 1" in line: current_tier = "Tier 1: True Allies"
        elif "TIER 2" in line: current_tier = "Tier 2: Battle Tested"
        elif "TIER 3" in line: current_tier = "Tier 3: Folded/Neutral"
        elif "TIER 4" in line: current_tier = "Tier 4: The Enemy"
        continue

    # 2. Skip Metadata/Header rows
    if "Ticker,Company" in line or line.startswith("Proven Receipts") or line == ",,":
        continue

    # 3. Process Data Rows
    match = ticker_pattern.match(line)
    if match:
        # This is a new company row
        parts = line.split(',', 2) # Split into Ticker, Company, Reason
        if len(parts) == 3:
            ticker = parts[0]
            company = parts[1]
            reason = parts[2]
            data.append({
                'Tier': current_tier,
                'Ticker': ticker,
                'Company': company,
                'Reason': reason
            })
    elif line and data:
        # This is a continuation line (e.g. "Refused to fold...")
        # Append this text to the LAST company added
        data[-1]['Reason'] += " " + line

# Create DataFrame
df = pd.DataFrame(data)

# 4. Clean the "Reason" text (Remove tags)
df['Reason'] = df['Reason'].str.replace(r'', '', regex=True).str.strip()

# 5. (Bonus) Extract Money mentions using Regex
def extract_money(text):
    # Finds patterns like $120M, $500M, $1B
    match = re.search(r'\$(\d+(?:\.\d+)?)\s*(M|B|Million|Billion)', text, re.IGNORECASE)
    if match:
        amount = float(match.group(1))
        unit = match.group(2).upper()
        if 'B' in unit: return amount * 1_000_000_000
        if 'M' in unit: return amount * 1_000_000
    return 0

df['Est_Investment_Value'] = df['Reason'].apply(extract_money)

print(df.head())
df.to_csv('Cleaned_Corporate_Data.csv', index=False)