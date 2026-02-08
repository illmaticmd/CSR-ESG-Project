import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CSR & ESG Risk Monitor",
    page_icon="📊",
    layout="wide"
)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Ready_For_PowerBI.csv')
    df = pd.read_csv(file_path)
    # Basic cleaning for the AI
    df = df.dropna(subset=['Tier', 'Reason'])
    df['Tier_Label'] = df['Tier'].apply(lambda x: x.split(':')[0])
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File not found! Please make sure 'Ready_For_PowerBI.csv' is in the same folder.")
    st.stop()

# --- TRAIN AI MODEL (ON THE FLY) ---
# Since the dataset is small, we can train the AI every time the app loads.
# This ensures the AI always learns from the latest data.
@st.cache_resource
def train_model(data):
    # 1. Vectorize
    tfidf = TfidfVectorizer(stop_words='english', max_features=500)
    X = tfidf.fit_transform(data['Reason'])
    y = data['Tier_Label']
    
    # 2. Train
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    return model, tfidf

model, vectorizer = train_model(df)

# --- SIDEBAR (NAVIGATION & AI) ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to:", ["Dashboard", "AI Predictor"])

st.sidebar.markdown("---")
st.sidebar.header("Filter Options (Dashboard Only)")

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

# --- PAGE 1: DASHBOARD ---
if page == "Dashboard":
    st.title("📊 Corporate Social Responsibility Monitor")
    st.markdown("## Tracking Corporate Alignment & Committed Capital")

    # Metrics
    total_capital = df_selection['Committed_Capital'].sum()
    avg_market_cap = df_selection['Market_Cap'].mean()
    total_companies = df_selection.shape[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Committed Capital", f"${total_capital:,.0f}")
    c2.metric("Avg Market Cap", f"${avg_market_cap:,.0f}")
    c3.metric("Companies Tracked", total_companies)

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Alignment Distribution")
        fig_tier = px.pie(
            df_selection, names='Tier', hole=0.4, color='Tier',
            color_discrete_map={
                "Tier 1: True Allies": "#00CC96",
                "Tier 2: Battle Tested": "#636EFA",
                "Tier 3: Folded/Neutral": "#FECB52",
                "Tier 4: The Enemy": "#EF553B"
            }
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    with col2:
        st.subheader("Capital by Sector")
        sector_group = df_selection.groupby('Sector')['Committed_Capital'].sum().reset_index()
        fig_sector = px.bar(
            sector_group, x='Committed_Capital', y='Sector', orientation='h',
            title='Total Committed Capital by Sector', text_auto='.2s'
        )
        fig_sector.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_sector, use_container_width=True)

    st.markdown("---")
    st.dataframe(df_selection[['Tier', 'Ticker', 'Company', 'Reason', 'Sector']])

# --- PAGE 2: AI PREDICTOR ---
elif page == "AI Predictor":
    st.title("🤖 ESG Risk Classifier")
    st.markdown("""
    This AI model is trained on the dataset to detect **Corporate Alignment** based on text descriptions.
    **Top Keywords learned by model:** *Safe, Black, Racism, Lawsuit*
    """)
    
    st.markdown("### Test the Model")
    user_input = st.text_area("Enter a company description (e.g. 'Facing a lawsuit for discrimination'):", height=100)
    
    if st.button("Analyze Risk"):
        if user_input:
            # 1. Transform input to numbers
            vec_input = vectorizer.transform([user_input])
            # 2. Predict
            prediction = model.predict(vec_input)[0]
            # 3. Get Probability (Confidence)
            probs = model.predict_proba(vec_input)[0]
            confidence = max(probs) * 100
            
            st.markdown("---")
            st.subheader(f"Prediction: {prediction}")
            st.write(f"Confidence: **{confidence:.1f}%**")
            
            if "Tier 1" in prediction:
                st.success("This sounds like an ALLY.")
            elif "Tier 4" in prediction:
                st.error("This sounds like a RISK.")
            else:
                st.warning("This sounds Neutral or Mixed.")
        else:
            st.warning("Please enter text first.")