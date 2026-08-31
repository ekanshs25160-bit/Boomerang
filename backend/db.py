import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'risk_audit.db')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_used TEXT NOT NULL,
                optimal_threshold REAL NOT NULL,
                n_orders_scored INTEGER NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_decisions (
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                order_id TEXT NOT NULL,
                risk_score REAL NOT NULL,
                flagged BOOLEAN NOT NULL,
                top_factors TEXT NOT NULL,
                human_action TEXT,
                action_timestamp TEXT,
                FOREIGN KEY (run_id) REFERENCES detection_runs (run_id)
            )
        ''')
        
        conn.commit()

def record_detection_run(model_used, optimal_threshold, orders_data):
    """
    Records a detection run and all associated order decisions.
    orders_data should be a list of dicts containing order info and risk scores.
    """
    timestamp = datetime.utcnow().isoformat()
    n_orders_scored = len(orders_data)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO detection_runs (timestamp, model_used, optimal_threshold, n_orders_scored)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, model_used, optimal_threshold, n_orders_scored))
        
        run_id = cursor.lastrowid
        
        for order in orders_data:
            cursor.execute('''
                INSERT INTO order_decisions 
                (run_id, order_id, risk_score, flagged, top_factors)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                run_id,
                order['order_id'],
                order['risk_score'],
                order['risk_score'] >= optimal_threshold,
                json.dumps(order['top_factors'])
            ))
            
        conn.commit()
        return run_id

def record_human_action(order_id, action):
    """
    Records a human action ('approved', 'declined', 'info_requested') for a specific order.
    """
    timestamp = datetime.utcnow().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Note: In a real app we might want to update the most recent decision for this order, 
        # or handle multiple runs. We'll update the row where human_action IS NULL.
        cursor.execute('''
            UPDATE order_decisions
            SET human_action = ?, action_timestamp = ?
            WHERE order_id = ? AND human_action IS NULL
        ''', (action, timestamp, order_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        return rows_affected > 0

def get_audit_log(limit=50):
    """
    Retrieves the latest detection runs and their associated order decisions.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT run_id, timestamp, model_used, optimal_threshold, n_orders_scored
            FROM detection_runs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        runs = [dict(row) for row in cursor.fetchall()]
        
        for run in runs:
            cursor.execute('''
                SELECT decision_id, order_id, risk_score, flagged, top_factors, human_action, action_timestamp
                FROM order_decisions
                WHERE run_id = ?
            ''', (run['run_id'],))
            
            run['decisions'] = [dict(row) for row in cursor.fetchall()]
            # Parse JSON strings back to lists for the API
            for decision in run['decisions']:
                decision['top_factors'] = json.loads(decision['top_factors'])
                decision['flagged'] = bool(decision['flagged'])
                
        return runs
