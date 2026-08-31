import os
import pickle
import pandas as pd
from flask import Flask, jsonify, render_template, request
import db

app = Flask(__name__)

# Initialize SQLite database
try:
    db.init_db()
except Exception as e:
    print(f"Failed to initialize database: {e}")

# Base directory is one level up from backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load artifacts globally
artifacts = None
model = None
opt_threshold = 0.5
feature_names = []

try:
    with open(os.path.join(BASE_DIR, 'models', 'model_artifacts.pkl'), 'rb') as f:
        artifacts = pickle.load(f)
        model = artifacts['logistic_regression']['model']
        opt_threshold = artifacts['logistic_regression']['optimal_threshold']
        feature_names = artifacts['logistic_regression']['feature_names']
except Exception as e:
    print(f"Failed to load artifacts: {e}")

# Load orders globally
try:
    df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'synthetic_returns_data.csv'))
    high_risk = df[df['is_abusive_return'] == 1].sample(min(10, len(df[df['is_abusive_return'] == 1])), random_state=42)
    low_risk = df[df['is_abusive_return'] == 0].sample(20 - len(high_risk), random_state=42)
    orders_df = pd.concat([high_risk, low_risk]).sample(frac=1, random_state=42).reset_index(drop=True)
except Exception as e:
    print(f"Failed to load data: {e}")
    orders_df = pd.DataFrame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/orders')
def get_orders():
    if model is None or orders_df.empty:
        return jsonify({"error": "Model or data not loaded"}), 500
    features = orders_df.drop(columns=['is_abusive_return', 'customer_type_DEBUG_ONLY', 'order_id', 'customer_id', 'address_id', 'payment_method_id'])
    probs = model.predict_proba(features)[:, 1]
    
    orders_data = []
    for idx, row in orders_df.iterrows():
        prob = float(probs[idx])
        
        # Calculate top factors for this specific order
        order_features = features.iloc[[idx]]
        transformed = model.named_steps['preprocessor'].transform(order_features)
        coef = model.named_steps['classifier'].coef_[0]
        contributions = transformed[0] * coef
        
        contrib_df = pd.DataFrame({'Feature': feature_names, 'Contribution': contributions})
        top_factors_df = contrib_df[contrib_df['Contribution'] > 0].sort_values(by='Contribution', ascending=False).head(3)
        
        top_factors = []
        for _, r in top_factors_df.iterrows():
            feat = r['Feature']
            feat_clean = feat.replace('_', ' ').title()
            if feat.startswith('item_category_'):
                feat_clean = f"Item Category: {feat.replace('item_category_', '').title()}"
            elif feat.startswith('payment_method_type_'):
                feat_clean = f"Payment Method: {feat.replace('payment_method_type_', '').upper()}"
                
            val = row.get(feat, "True" if "item_category" in feat or "payment_method" in feat else "Detected")
            top_factors.append({
                "feature": feat_clean,
                "contribution": float(r['Contribution']),
                "value": str(val)
            })
            
        orders_data.append({
            "order_id": row['order_id'],
            "customer_id": row['customer_id'],
            "account_age_days": int(row['account_age_days']),
            "order_value": float(row['order_value']),
            "total_past_orders": int(row['total_past_orders']),
            "historical_return_rate": float(row['historical_return_rate']),
            "address_reuse": bool(row['address_reuse_across_accounts']),
            "orders_in_last_24h": int(row['orders_in_last_24h']),
            "risk_score": prob,
            "threshold": opt_threshold,
            "top_factors": top_factors
        })
        
    # Persist the detection run and order decisions to the database
    try:
        db.record_detection_run('logistic_regression', opt_threshold, orders_data)
    except Exception as e:
        print(f"Failed to record detection run: {e}")
        
    return jsonify(orders_data)

@app.route('/api/orders/<order_id>/action', methods=['POST'])
def record_order_action(order_id):
    data = request.json
    action = data.get('action')
    
    if not action or action not in ['approved', 'declined', 'info_requested']:
        return jsonify({"error": "Invalid action"}), 400
        
    try:
        success = db.record_human_action(order_id, action)
        if success:
            return jsonify({"status": "success", "message": f"Action '{action}' recorded for order {order_id}"})
        else:
            return jsonify({"error": "Order not found or action already recorded"}), 404
    except Exception as e:
        print(f"Failed to record action: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/audit-log')
def get_audit_log():
    try:
        limit = int(request.args.get('limit', 50))
        runs = db.get_audit_log(limit)
        return jsonify(runs)
    except Exception as e:
        print(f"Failed to fetch audit log: {e}")
        return jsonify({"error": "Database error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
