import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. LOAD & CLEAN DATA ---
print("Step 1: Loading Data...")
df = pd.read_csv('Ready_For_PowerBI.csv')

# Drop rows where 'Tier' or 'Reason' is missing
df = df.dropna(subset=['Tier', 'Reason'])

# Simplify Tiers to just the number (e.g., "Tier 1") for easier reading
df['Tier_Label'] = df['Tier'].apply(lambda x: x.split(':')[0])

print(f"Loaded {len(df)} companies.")
print(df['Tier_Label'].value_counts())

# --- 2. PREPROCESSING (NLP) ---
print("\nStep 2: Vectorizing Text (Turning words into numbers)...")

# TF-IDF: Term Frequency - Inverse Document Frequency
# This highlights "rare but important" words (like 'Lawsuit') over common words (like 'The')
tfidf = TfidfVectorizer(stop_words='english', max_features=1000)

# X = The Features (The Text), y = The Target (The Tier)
X = tfidf.fit_transform(df['Reason'])
y = df['Tier_Label']

# Split: 80% of data to Train, 20% to Test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- 3. TRAIN MODEL ---
print("\nStep 3: Training Random Forest Classifier...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("Model Trained Successfully!")

# --- 4. EVALUATE ---
print("\nStep 4: Evaluation Results:")
y_pred = model.predict(X_test)

# Print Accuracy and stats
print(classification_report(y_test, y_pred))

# --- 5. EXPLAINABILITY (The "Why") ---
# This part extracts which words drive the decision for each Tier
print("\nStep 5: Top Keywords Driving Predictions:")

feature_names = tfidf.get_feature_names_out()
importances = model.feature_importances_

# Get the indices of the most important words
sorted_indices = np.argsort(importances)[::-1]

print("Top 20 Most Influential Words in the Dataset:")
for i in range(20):
    word = feature_names[sorted_indices[i]]
    score = importances[sorted_indices[i]]
    print(f"{i+1}. {word} ({score:.4f})")

# Bonus: Let's test it on a fake new company
print("\n--- LIVE TEST ---")
new_reviews = [
    "Company donated $5M to HBCUs and supported voting rights.",
    "Facing a class action lawsuit for racial discrimination and toxicity.",
    "Refused to comment on social issues. Stays neutral."
]

print("Predicting Tiers for new descriptions:")
new_vectors = tfidf.transform(new_reviews)
predictions = model.predict(new_vectors)

for text, pred in zip(new_reviews, predictions):
    print(f"Text: '{text}' -> Prediction: {pred}")