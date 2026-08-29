import numpy as np
import pandas as pd
import uuid

def generate_synthetic_data(n_customers=5000, n_orders=10000):
    np.random.seed(42)
    
    # --- 1. GENERATE CUSTOMERS ---
    customer_types = ['normal', 'serial_returner', 'wardrober', 'bracketer', 'ring_member']
    probs = [0.86, 0.05, 0.04, 0.03, 0.02]
    assigned_types = np.random.choice(customer_types, size=n_customers, p=probs)
    
    customers = pd.DataFrame({
        'customer_id': [str(uuid.uuid4())[:8] for _ in range(n_customers)],
        'customer_type_DEBUG_ONLY': assigned_types
    })
    
    # Base Customer History
    customers['account_age_days'] = np.random.randint(1, 1800, n_customers)
    customers['total_past_orders'] = np.random.poisson(lam=5, size=n_customers)
    customers['historical_return_rate'] = np.random.beta(a=1, b=10, size=n_customers)
    
    serial_idx = customers['customer_type_DEBUG_ONLY'] == 'serial_returner'
    customers.loc[serial_idx, 'total_past_orders'] = np.random.poisson(lam=20, size=serial_idx.sum())
    customers.loc[serial_idx, 'historical_return_rate'] = np.random.beta(a=5, b=2, size=serial_idx.sum())
    
    ring_idx = customers['customer_type_DEBUG_ONLY'] == 'ring_member'
    customers.loc[ring_idx, 'account_age_days'] = np.random.randint(1, 30, size=ring_idx.sum())
    customers.loc[ring_idx, 'total_past_orders'] = np.random.poisson(lam=1, size=ring_idx.sum())
    
    customers['historical_return_rate'] = np.where(customers['total_past_orders'] == 0, 0, customers['historical_return_rate'])
    
    customers['historical_return_value_rate'] = np.clip(customers['historical_return_rate'] + np.random.normal(0, 0.05, n_customers), 0, 1)
    wardrober_idx = customers['customer_type_DEBUG_ONLY'] == 'wardrober'
    customers.loc[wardrober_idx, 'historical_return_value_rate'] = np.clip(customers.loc[wardrober_idx, 'historical_return_rate'] + np.random.uniform(0.1, 0.3, size=wardrober_idx.sum()), 0, 1)
    
    customers['days_since_last_return'] = np.where(customers['total_past_orders'] > 0, np.random.randint(1, 365, n_customers), -1)
    customers.loc[serial_idx, 'days_since_last_return'] = np.random.randint(1, 14, size=serial_idx.sum())
    
    # --- 2. GENERATE ORDERS ---
    # Sample customers to create orders
    # Give some customers more orders
    order_customer_indices = np.random.choice(customers.index, size=n_orders, replace=True)
    
    df = customers.iloc[order_customer_indices].copy().reset_index(drop=True)
    df['order_id'] = [f"ORD-{str(uuid.uuid4())[:8].upper()}" for _ in range(n_orders)]
    
    # Order's Characteristics
    df['order_value'] = np.round(np.random.lognormal(mean=7, sigma=1, size=n_orders), 2)
    wardrober_order_idx = df['customer_type_DEBUG_ONLY'] == 'wardrober'
    df.loc[wardrober_order_idx, 'order_value'] = np.round(np.random.lognormal(mean=9, sigma=0.5, size=wardrober_order_idx.sum()), 2)
    
    categories = ['apparel', 'electronics', 'home', 'beauty', 'grocery']
    df['item_category'] = np.random.choice(categories, size=n_orders, p=[0.4, 0.25, 0.15, 0.1, 0.1])
    df.loc[wardrober_order_idx | (df['customer_type_DEBUG_ONLY'] == 'bracketer'), 'item_category'] = 'apparel'
    
    df['quantity'] = np.random.randint(1, 6, n_orders)
    df['is_multi_variant_order'] = (np.random.rand(n_orders) < 0.1).astype(int)
    bracketer_order_idx = df['customer_type_DEBUG_ONLY'] == 'bracketer'
    df.loc[bracketer_order_idx, 'quantity'] = np.random.randint(3, 10, size=bracketer_order_idx.sum())
    df.loc[bracketer_order_idx, 'is_multi_variant_order'] = (np.random.rand(bracketer_order_idx.sum()) < 0.9).astype(int)
    
    df['discount_pct_applied'] = np.random.choice([0, 10, 20, 30], n_orders, p=[0.5, 0.3, 0.15, 0.05])
    
    # Address/Identity Signals
    df['shipping_billing_mismatch'] = (np.random.rand(n_orders) < 0.1).astype(int)
    df.loc[wardrober_order_idx, 'shipping_billing_mismatch'] = (np.random.rand(wardrober_order_idx.sum()) < 0.6).astype(int)
    
    ring_order_idx = df['customer_type_DEBUG_ONLY'] == 'ring_member'
    df['is_new_shipping_address'] = (np.random.rand(n_orders) < 0.1).astype(int)
    df.loc[ring_order_idx, 'is_new_shipping_address'] = (np.random.rand(ring_order_idx.sum()) < 0.8).astype(int)
    
    df['address_reuse_across_accounts'] = (np.random.rand(n_orders) < 0.02).astype(int)
    df.loc[ring_order_idx, 'address_reuse_across_accounts'] = (np.random.rand(ring_order_idx.sum()) < 0.9).astype(int)
    
    # Payment Signals
    df['payment_method_type'] = np.random.choice(['prepaid', 'COD'], n_orders, p=[0.7, 0.3])
    df.loc[ring_order_idx, 'payment_method_type'] = np.random.choice(['prepaid', 'COD'], size=ring_order_idx.sum(), p=[0.2, 0.8])
    
    df['is_new_payment_method'] = (np.random.rand(n_orders) < 0.15).astype(int)
    df.loc[ring_order_idx, 'is_new_payment_method'] = (np.random.rand(ring_order_idx.sum()) < 0.7).astype(int)
    
    df['payment_method_reuse_across_accounts'] = (np.random.rand(n_orders) < 0.03).astype(int)
    df.loc[ring_order_idx, 'payment_method_reuse_across_accounts'] = (np.random.rand(ring_order_idx.sum()) < 0.85).astype(int)
    
    # Velocity Signals
    df['orders_in_last_24h'] = np.random.poisson(lam=0.2, size=n_orders)
    df.loc[ring_order_idx, 'orders_in_last_24h'] = np.random.poisson(lam=3, size=ring_order_idx.sum())
    
    df['orders_in_last_24h_same_address'] = np.where(df['orders_in_last_24h'] > 0, np.random.randint(0, 2, n_orders), 0)
    df.loc[ring_order_idx, 'orders_in_last_24h_same_address'] = np.where(df.loc[ring_order_idx, 'orders_in_last_24h'] > 0, np.random.randint(1, 4, ring_order_idx.sum()), 0)
    
    # --- 3. INJECTING FRAUD PATTERNS PROBABILISTICALLY ---
    risk_score = np.zeros(n_orders)
    risk_score += 0.01 
    
    risk_score += np.where((df['historical_return_rate'] > 0.5) & (df['total_past_orders'] > 3), 0.3, 0)
    risk_score += np.where((df['historical_return_rate'] > 0.8), 0.3, 0)
    
    risk_score += np.where((df['is_multi_variant_order'] == 1) & (df['item_category'] == 'apparel') & (df['quantity'] > 2), 0.4, 0)
    
    risk_score += np.where((df['order_value'] > 5000) & (df['item_category'] == 'apparel') & (df['shipping_billing_mismatch'] == 1), 0.35, 0)
    risk_score += np.where((df['historical_return_value_rate'] > df['historical_return_rate'] + 0.1) & (df['order_value'] > 3000), 0.2, 0)
    
    risk_score += np.where(df['address_reuse_across_accounts'] == 1, 0.4, 0)
    risk_score += np.where(df['payment_method_reuse_across_accounts'] == 1, 0.3, 0)
    risk_score += np.where((df['payment_method_type'] == 'COD') & (df['orders_in_last_24h_same_address'] >= 2), 0.35, 0)
    
    risk_score += np.where((df['days_since_last_return'] > 0) & (df['days_since_last_return'] < 7), 0.15, 0)
    
    risk_prob = np.clip(risk_score, 0.005, 0.95)
    df['is_abusive_return'] = np.random.binomial(1, risk_prob)
    
    # Reorder columns for neatness
    cols = ['order_id', 'customer_id', 'customer_type_DEBUG_ONLY', 'account_age_days', 
            'total_past_orders', 'historical_return_rate', 'historical_return_value_rate', 
            'days_since_last_return', 'order_value', 'item_category', 'quantity', 
            'is_multi_variant_order', 'discount_pct_applied', 'shipping_billing_mismatch', 
            'is_new_shipping_address', 'address_reuse_across_accounts', 'payment_method_type', 
            'is_new_payment_method', 'payment_method_reuse_across_accounts', 'orders_in_last_24h', 
            'orders_in_last_24h_same_address', 'is_abusive_return']
    
    df = df[cols]
    return df

if __name__ == "__main__":
    df = generate_synthetic_data()
    df.to_csv('synthetic_returns_data.csv', index=False)
    print(f"Generated {len(df)} records.")
    print(f"Overall fraud rate: {df['is_abusive_return'].mean():.2%}")
    print("\nFraud rate by assigned customer type (for sanity check):")
    print(df.groupby('customer_type_DEBUG_ONLY')['is_abusive_return'].mean())
