import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CSR & ESG Risk Monitor",
    page_icon="📊",
    layout="wide"
)

# --- LOAD DATA ---
@st.cache_data # This makes the app fast by remembering the data
def load_data():
    # Get the folder where this script is running
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Ready_For_PowerBI.csv')
    
    # Load CSV
    df = pd.read_csv(file_path)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File not found! Please make sure 'Ready_For_PowerBI.csv' is in the same folder.")
    st.stop()

# --- SIDEBAR (FILTERS) ---
st.sidebar.header("Filter Options")

# Filter by Tier
tier_options = st.sidebar.multiselect(
    "Select Tiers:",
    options=df['Tier'].unique(),
    default=df['Tier'].unique()
)

# Filter by Sector
sector_options = st.sidebar.multiselect(
    "Select Sectors:",
    options=df['Sector'].unique(),
    default=df['Sector'].unique()
)

# Apply Filters
df_selection = df.query(
    "Tier == @tier_options & Sector == @sector_options"
)

# --- MAIN PAGE ---
st.title("📊 Corporate Social Responsibility (CSR) Monitor")
st.markdown("## Tracking Corporate Alignment & Committed Capital")

# --- TOP KPI METRICS ---
total_capital = df_selection['Committed_Capital'].sum()
avg_market_cap = df_selection['Market_Cap'].mean()
total_companies = df_selection.shape[0]

# Create 3 columns for metrics
left_column, middle_column, right_column = st.columns(3)

with left_column:
    st.metric(label="Total Committed Capital", value=f"${total_capital:,.0f}")
with middle_column:
    st.metric(label="Avg Market Cap", value=f"${avg_market_cap:,.0f}")
with right_column:
    st.metric(label="Companies Tracked", value=total_companies)

st.markdown("---")

# --- CHARTS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Alignment Distribution")
    # A Donut Chart showing the breakdown of Tiers
    fig_tier = px.pie(
        df_selection, 
        names='Tier', 
        title='Companies by Alignment Tier',
        hole=0.4,
        color='Tier',
        # Custom colors for impact (Green for Allies, Red for Enemies)
        color_discrete_map={
            "Tier 1: True Allies": "#00CC96", # Green
            "Tier 2: Battle Tested": "#636EFA", # Blue
            "Tier 3: Folded/Neutral": "#FECB52", # Yellow
            "Tier 4: The Enemy": "#EF553B" # Red
        }
    )
    st.plotly_chart(fig_tier, use_container_width=True)

with col2:
    st.subheader("Capital by Sector")
    # A Bar Chart showing which industries are spending the most
    # We group by Sector first to sum the capital
    sector_group = df_selection.groupby('Sector')['Committed_Capital'].sum().reset_index()
    
    fig_sector = px.bar(
        sector_group, 
        x='Committed_Capital', 
        y='Sector', 
        orientation='h',
        title='Total Committed Capital by Sector',
        text_auto='.2s' # Shows simplified numbers (e.g. 1.2B)
    )
    # Sort bars so biggest is on top
    fig_sector.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_sector, use_container_width=True)

# --- RAW DATA TABLE ---
st.markdown("---")
st.subheader("📋 The Receipts (Detailed Data)")
st.dataframe(df_selection[['Tier', 'Ticker', 'Company', 'Reason', 'Sector', 'Committed_Capital']])

# --- FOOTER ---
st.markdown("built with **Streamlit** & **Python**")