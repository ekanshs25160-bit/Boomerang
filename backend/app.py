import os
import pickle
import pandas as pd
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import db

app = Flask(__name__)
CORS(app)

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

import subprocess

# Load orders globally
orders_df = pd.DataFrame()

def load_data():
    global orders_df
    try:
        df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'synthetic_returns_data.csv'))
        high_risk = df[df['is_abusive_return'] == 1].sample(min(10, len(df[df['is_abusive_return'] == 1])), random_state=42)
        low_risk = df[df['is_abusive_return'] == 0].sample(20 - len(high_risk), random_state=42)
        orders_df = pd.concat([high_risk, low_risk]).sample(frac=1, random_state=42).reset_index(drop=True)
    except Exception as e:
        print(f"Failed to load data: {e}")
        orders_df = pd.DataFrame()

load_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-data', methods=['POST'])
def generate_data_endpoint():
    try:
        result = subprocess.run(['python3', os.path.join(BASE_DIR, 'ml', 'generate_data.py')], capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({"error": "Failed to generate data", "details": result.stderr}), 500
        load_data()
        return jsonify({"success": True, "message": "New data generated!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
                "name": feat_clean,
                "impact": float(r['Contribution']),
                "value": str(val),
                "severity": "high" if float(r['Contribution']) > 0.5 else "medium" if float(r['Contribution']) > 0.2 else "info"
            })
            
        orders_data.append({
            "order_id": row['order_id'],
            "customer_id": row['customer_id'],
            "created_at": "2026-08-31T10:15:00Z",
            "order_value": float(row['order_value']),
            "risk_score": prob,
            "flagged": bool(prob >= opt_threshold),
            "status": "pending",
            "top_factors": top_factors,
            "customer_profile": {
                "account_age_days": int(row['account_age_days']),
                "past_orders": int(row['total_past_orders']),
                "historical_return_rate": float(row['historical_return_rate'])
            }
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

@app.route('/api/overview')
def get_overview():
    stats = db.get_overview_stats()
    if not stats:
        return jsonify({"error": "No data"}), 404
        
    total_accounts = orders_df['customer_id'].nunique() if not orders_df.empty else 0
    total_transactions = len(orders_df) if not orders_df.empty else 0
    
    return jsonify({
        "total_accounts": total_accounts,
        "total_transactions": total_transactions,
        "total_scored": stats['total_scored'] or 0,
        "flagged_count": stats['flagged_count'] or 0,
        "risk_distribution": {
            "low": stats['risk_low'] or 0,
            "medium": stats['risk_medium'] or 0,
            "high": stats['risk_high'] or 0
        },
        "queue_status": {
            "new": stats['queue_new'] or 0,
            "reviewing": 0,
            "approved": stats['queue_approved'] or 0,
            "declined": stats['queue_declined'] or 0
        }
    })

@app.route('/api/audit-log')
def get_audit_log():
    try:
        limit = int(request.args.get('limit', 50))
        runs = db.get_audit_log(limit)
        return jsonify(runs)
    except Exception as e:
        print(f"Failed to fetch audit log: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/rings')
def get_rings():
    min_score = request.args.get('min_score')
    status = request.args.get('status')
    
    try:
        rings = db.get_detected_rings(min_score=min_score, status=status)
        return jsonify(rings)
    except Exception as e:
        print(f"Failed to fetch rings: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/rings/<ring_id>')
def get_ring_detail(ring_id):
    try:
        ring = db.get_detected_ring(ring_id)
        if not ring:
            return jsonify({"error": "Ring not found"}), 404
            
        accounts = [{"id": m} for m in ring['members']]
        entity_type = "Address" if ring['shared_entity_type'] == 'address' else "Payment"
        entities = [{"id": ring['shared_entity_id'], "type": entity_type}]
        links = [{"source": m, "target": ring['shared_entity_id']} for m in ring['members']]
        
        return jsonify({
            "summary_stats": {
                "total_accounts": ring['member_count'],
                "shared_entities": 1,
                "group_abuse_rate": ring['group_abuse_rate'],
                "status": ring['status'],
                "risk_level": ring['risk_level']
            },
            "dynamic_chips": ring['dynamic_chips'],
            "graph_data": {
                "accounts": accounts,
                "entities": entities,
                "links": links
            }
        })
    except Exception as e:
        print(f"Failed to fetch ring details: {e}")
        return jsonify({"error": "Database error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
