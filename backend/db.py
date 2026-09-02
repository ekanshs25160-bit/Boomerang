import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'risk_audit.db')

@contextmanager
def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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
        
        cursor.execute("DROP TABLE IF EXISTS detected_rings")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detected_rings (
                ring_id TEXT PRIMARY KEY,
                run_id INTEGER NOT NULL,
                member_count INTEGER NOT NULL,
                shared_entity_type TEXT NOT NULL,
                shared_entity_id TEXT NOT NULL,
                group_abuse_rate REAL NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TEXT NOT NULL,
                members TEXT NOT NULL,
                dynamic_chips TEXT NOT NULL
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
                decision['flagged'] = bool(decision['flagged'])
                
        return runs

def get_overview_stats():
    """
    Retrieves aggregate stats for the most recent detection run.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(run_id) as latest_run FROM detection_runs")
        row = cursor.fetchone()
        latest_run = row['latest_run'] if row and row['latest_run'] else None
        
        if not latest_run:
            return None
            
        cursor.execute("""
            SELECT 
                COUNT(*) as total_scored,
                SUM(CASE WHEN flagged = 1 THEN 1 ELSE 0 END) as flagged_count,
                SUM(CASE WHEN risk_score < 0.33 THEN 1 ELSE 0 END) as risk_low,
                SUM(CASE WHEN risk_score >= 0.33 AND risk_score < 0.66 THEN 1 ELSE 0 END) as risk_medium,
                SUM(CASE WHEN risk_score >= 0.66 THEN 1 ELSE 0 END) as risk_high,
                SUM(CASE WHEN human_action IS NULL THEN 1 ELSE 0 END) as queue_new,
                SUM(CASE WHEN human_action = 'approved' THEN 1 ELSE 0 END) as queue_approved,
                SUM(CASE WHEN human_action = 'declined' THEN 1 ELSE 0 END) as queue_declined
            FROM order_decisions
            WHERE run_id = ?
        """, (latest_run,))
        
        return dict(cursor.fetchone())

def record_detected_rings(rings_data):
    timestamp = datetime.utcnow().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO detection_runs (timestamp, model_used, optimal_threshold, n_orders_scored)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, 'ring_detector', 0.0, len(rings_data)))
        run_id = cursor.lastrowid
        
        for ring in rings_data:
            cursor.execute('''
                INSERT INTO detected_rings 
                (ring_id, run_id, member_count, shared_entity_type, shared_entity_id, group_abuse_rate, risk_level, status, created_at, members, dynamic_chips)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?, ?, ?)
            ''', (
                ring['ring_id'],
                run_id,
                ring['member_count'],
                ring['shared_entity_type'],
                ring['shared_entity_id'],
                ring['group_abuse_rate'],
                ring['risk_level'],
                timestamp,
                json.dumps(ring['members']),
                json.dumps(ring.get('dynamic_chips', []))
            ))
        conn.commit()
        return run_id

def get_detected_rings(min_score=None, status=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM detected_rings WHERE 1=1"
        params = []
        
        if min_score is not None:
            query += " AND group_abuse_rate >= ?"
            params.append(float(min_score) / 100.0) # assuming min_score is percentage
            
        if status and status != 'All':
            query += " AND status = ?"
            params.append(status.lower())
            
        query += " ORDER BY group_abuse_rate DESC, created_at DESC"
        
        cursor.execute(query, params)
        rings = [dict(row) for row in cursor.fetchall()]
        
        for r in rings:
            r['members'] = json.loads(r['members'])
            r['dynamic_chips'] = json.loads(r['dynamic_chips']) if 'dynamic_chips' in r else []
            
        return rings

def get_detected_ring(ring_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detected_rings WHERE ring_id = ?", (ring_id,))
        row = cursor.fetchone()
        if not row:
            return None
        ring = dict(row)
        ring['members'] = json.loads(ring['members'])
        ring['dynamic_chips'] = json.loads(ring['dynamic_chips']) if 'dynamic_chips' in ring else []
        return ring
