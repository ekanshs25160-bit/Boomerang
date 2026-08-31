import pandas as pd
import numpy as np
import pickle
from sklearn.metrics import recall_score, precision_score

print("Loading data and model...")
df = pd.read_csv('synthetic_returns_data.csv')
with open('model_artifacts.pkl', 'rb') as f:
    artifacts = pickle.load(f)

model = artifacts['model']
optimal_threshold = artifacts['optimal_threshold']

# Let's predict on the entire dataset to see the breakdown, or we can just look at the whole dataset
X = df.drop(columns=['is_abusive_return', 'customer_type_DEBUG_ONLY', 'order_id', 'customer_id'])
y = df['is_abusive_return']

y_probs = model.predict_proba(X)[:, 1]
y_pred_opt = (y_probs >= optimal_threshold).astype(int)

df['pred'] = y_pred_opt
df['prob'] = y_probs

print(f"\n--- Recall & Precision Breakdown by Customer Type (Threshold={optimal_threshold:.4f}) ---")
for ctype in df['customer_type_DEBUG_ONLY'].unique():
    subset = df[df['customer_type_DEBUG_ONLY'] == ctype]
    y_true = subset['is_abusive_return']
    y_pred = subset['pred']
    
    if len(y_true) > 0 and sum(y_true) > 0:
        recall = recall_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        print(f"{ctype:15s} | N: {len(subset):4d} | Abusive: {sum(y_true):4d} | Recall: {recall:.4f} | Precision: {precision:.4f}")

