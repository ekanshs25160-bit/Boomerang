"""
Synthetic data generator for the Return-Risk Scorer (Razorpay Buildathon - Track 02).

v2 changes from the first pass:
  1. FIXED LOOK-AHEAD LEAK: historical_return_rate, historical_return_value_rate,
     total_past_orders, and days_since_last_return are now computed SEQUENTIALLY,
     order by order, using only that customer's PRIOR orders. A customer's first
     order correctly shows zero history -- it no longer sees its own "eventual"
     lifetime return rate baked in from order #1.
  2. Reduced item_category over-reliance: wardrobers/bracketers now mostly target
     apparel but occasionally hit other categories, so the model can't fully
     substitute "category == apparel" for genuine behavioral signal.

Everything else (customer archetypes, risk_score formula, column names) is
kept consistent with v1 so train_eval.py / demo.py don't need schema changes.
"""

import numpy as np
import pandas as pd
import uuid
import os

def generate_synthetic_data(n_customers=5000, seed=42):
    rng = np.random.default_rng(seed)

    customer_types = ['normal', 'serial_returner', 'wardrober', 'bracketer', 'ring_member']
    probs = [0.86, 0.05, 0.04, 0.03, 0.02]
    assigned_types = rng.choice(customer_types, size=n_customers, p=probs)

    account_age_days = rng.integers(1, 1800, n_customers)
    ring_mask = assigned_types == 'ring_member'
    account_age_days = np.where(ring_mask, rng.integers(1, 30, n_customers), account_age_days)

    order_counts = rng.poisson(lam=2.2, size=n_customers) + 1
    order_counts = np.where(assigned_types == 'serial_returner',
                             rng.poisson(lam=6, size=n_customers) + 2, order_counts)
    order_counts = np.where(assigned_types == 'ring_member',
                             rng.poisson(lam=1.5, size=n_customers) + 1, order_counts)

    customer_ids = [str(uuid.uuid4())[:8] for _ in range(n_customers)]
    categories_pool = ['apparel', 'electronics', 'home', 'beauty', 'grocery']

    # --- ID Generation Setup ---
    id_rng = np.random.default_rng(seed + 1)
    
    # Pre-assign rings for ring_member customers
    ring_member_indices = np.where(assigned_types == 'ring_member')[0]
    n_rings = max(1, len(ring_member_indices) // 5) # average size 5 per ring
    
    ring_addresses = [f"ADDR-RING-{i}" for i in range(n_rings)]
    ring_payments = [f"PAY-RING-{i}" for i in range(n_rings)]
    
    # Pool for innocent reuse
    innocent_addresses = [f"ADDR-SHARED-{i}" for i in range(100)]
    innocent_payments = [f"PAY-SHARED-{i}" for i in range(100)]
    
    customer_ring_assignments = {}
    for i, idx in enumerate(ring_member_indices):
        ring_idx = i % n_rings
        customer_ring_assignments[idx] = ring_idx
    # ---------------------------

    rows = []

    for i in range(n_customers):
        ctype = assigned_types[i]
        cust_id = customer_ids[i]
        acct_age = account_age_days[i]
        n_orders = int(order_counts[i])

        past_orders = 0
        past_returns = 0
        past_order_value = 0.0
        past_returned_value = 0.0
        days_since_last_return = -1

        for order_num in range(n_orders):
            order_value = round(float(rng.lognormal(mean=7, sigma=1)), 2)
            if ctype == 'wardrober':
                order_value = round(float(rng.lognormal(mean=9, sigma=0.5)), 2)

            if ctype == 'wardrober':
                category = rng.choice(categories_pool, p=[0.72, 0.06, 0.05, 0.05, 0.12])
            elif ctype == 'bracketer':
                category = rng.choice(categories_pool, p=[0.70, 0.10, 0.05, 0.05, 0.10])
            elif ctype == 'serial_returner':
                category = rng.choice(categories_pool, p=[0.60, 0.20, 0.10, 0.05, 0.05])
            else:
                category = rng.choice(categories_pool, p=[0.4, 0.25, 0.15, 0.1, 0.1])

            quantity = int(rng.integers(1, 6))
            is_multi_variant = int(rng.random() < 0.1)
            if ctype == 'bracketer':
                quantity = int(rng.integers(3, 10))
                is_multi_variant = int(rng.random() < 0.9)
            elif ctype == 'serial_returner':
                quantity = int(rng.integers(2, 7))
                is_multi_variant = int(rng.random() < 0.4)

            discount_pct = int(rng.choice([0, 10, 20, 30], p=[0.5, 0.3, 0.15, 0.05]))

            shipping_billing_mismatch = int(rng.random() < 0.1)
            if ctype == 'wardrober':
                shipping_billing_mismatch = int(rng.random() < 0.6)

            is_new_shipping_address = int(rng.random() < 0.1)
            if ctype == 'ring_member':
                is_new_shipping_address = int(rng.random() < 0.8)

            address_reuse = int(rng.random() < 0.02)
            if ctype == 'ring_member':
                address_reuse = int(rng.random() < 0.9)

            payment_method_type = rng.choice(['prepaid', 'COD'], p=[0.7, 0.3])
            if ctype == 'ring_member':
                payment_method_type = rng.choice(['prepaid', 'COD'], p=[0.2, 0.8])

            is_new_payment_method = int(rng.random() < 0.15)
            if ctype == 'ring_member':
                is_new_payment_method = int(rng.random() < 0.7)

            payment_reuse = int(rng.random() < 0.03)
            if ctype == 'ring_member':
                payment_reuse = int(rng.random() < 0.85)

            # Assign concrete IDs based on the boolean flags
            if address_reuse == 1:
                if ctype == 'ring_member':
                    address_id = ring_addresses[customer_ring_assignments[i]]
                else:
                    address_id = id_rng.choice(innocent_addresses)
            else:
                address_id = f"ADDR-{uuid.uuid4().hex[:8]}"
                
            if payment_reuse == 1:
                if ctype == 'ring_member':
                    payment_id = ring_payments[customer_ring_assignments[i]]
                else:
                    payment_id = id_rng.choice(innocent_payments)
            else:
                payment_id = f"PAY-{uuid.uuid4().hex[:8]}"

            orders_last_24h = int(rng.poisson(lam=0.2))
            if ctype == 'ring_member':
                orders_last_24h = int(rng.poisson(lam=3))
            elif ctype == 'serial_returner':
                orders_last_24h = int(rng.poisson(lam=0.8))

            orders_last_24h_same_addr = 0
            if orders_last_24h > 0:
                orders_last_24h_same_addr = int(rng.integers(0, 2))
                if ctype == 'ring_member':
                    orders_last_24h_same_addr = int(rng.integers(1, 4))

            hist_return_rate = round(past_returns / past_orders, 4) if past_orders > 0 else 0.0
            hist_return_value_rate = round(past_returned_value / past_order_value, 4) if past_order_value > 0 else 0.0

            row = {
                'order_id': f"ORD-{str(uuid.uuid4())[:8].upper()}",
                'customer_id': cust_id,
                'customer_type_DEBUG_ONLY': ctype,
                'account_age_days': int(acct_age),
                'total_past_orders': past_orders,
                'historical_return_rate': hist_return_rate,
                'historical_return_value_rate': hist_return_value_rate,
                'days_since_last_return': days_since_last_return,
                'order_value': order_value,
                'item_category': category,
                'quantity': quantity,
                'is_multi_variant_order': is_multi_variant,
                'discount_pct_applied': discount_pct,
                'shipping_billing_mismatch': shipping_billing_mismatch,
                'is_new_shipping_address': is_new_shipping_address,
                'address_reuse_across_accounts': address_reuse,
                'address_id': address_id,
                'payment_method_type': payment_method_type,
                'is_new_payment_method': is_new_payment_method,
                'payment_method_reuse_across_accounts': payment_reuse,
                'payment_method_id': payment_id,
                'orders_in_last_24h': orders_last_24h,
                'orders_in_last_24h_same_address': orders_last_24h_same_addr,
            }

            risk_score = 0.01
            if hist_return_rate > 0.5 and past_orders > 3:
                risk_score += 0.3
            if hist_return_rate > 0.8:
                risk_score += 0.3
            # Serial returners have a genuine behavioral tendency that isn't purely
            # a function of already-observed history (real serial returners often
            # over-order variants/quantities "to try", intending some returns from
            # order one) -- without this, the archetype can't bootstrap a track
            # record from a cold start and becomes statistically invisible.
            if ctype == 'serial_returner':
                risk_score += 0.18
                if quantity >= 3:
                    risk_score += 0.12
            if is_multi_variant == 1 and category == 'apparel' and quantity > 2:
                risk_score += 0.4
            if order_value > 5000 and category == 'apparel' and shipping_billing_mismatch == 1:
                risk_score += 0.35
            if hist_return_value_rate > hist_return_rate + 0.1 and order_value > 3000:
                risk_score += 0.2
            if address_reuse == 1:
                risk_score += 0.4
            if payment_reuse == 1:
                risk_score += 0.3
            if payment_method_type == 'COD' and orders_last_24h_same_addr >= 2:
                risk_score += 0.35
            if 0 < days_since_last_return < 7:
                risk_score += 0.15

            risk_prob = min(0.95, max(0.005, risk_score))
            is_return = rng.random() < risk_prob
            row['is_abusive_return'] = int(is_return)
            rows.append(row)

            past_orders += 1
            past_order_value += order_value
            if is_return:
                past_returns += 1
                past_returned_value += order_value
                days_since_last_return = 1
            elif days_since_last_return >= 0:
                days_since_last_return += 30

    df = pd.DataFrame(rows)
    cols = ['order_id', 'customer_id', 'customer_type_DEBUG_ONLY', 'account_age_days',
            'total_past_orders', 'historical_return_rate', 'historical_return_value_rate',
            'days_since_last_return', 'order_value', 'item_category', 'quantity',
            'is_multi_variant_order', 'discount_pct_applied', 'shipping_billing_mismatch',
            'is_new_shipping_address', 'address_reuse_across_accounts', 'address_id', 'payment_method_type',
            'is_new_payment_method', 'payment_method_reuse_across_accounts', 'payment_method_id', 'orders_in_last_24h',
            'orders_in_last_24h_same_address', 'is_abusive_return']
    return df[cols]

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df = generate_synthetic_data()
    out_path = os.path.join(BASE_DIR, 'data', 'synthetic_returns_data.csv')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} records across {df['customer_id'].nunique()} customers.")
    print(f"Overall abuse rate: {df['is_abusive_return'].mean():.2%}")
    print("\nAbuse rate by assigned customer type (sanity check):")
    print(df.groupby('customer_type_DEBUG_ONLY')['is_abusive_return'].mean())
    print("\nFirst-order-only abuse rate (should be lower -- no history to lean on yet):")
    first_orders = df[df['total_past_orders'] == 0]
    print(f"  {first_orders['is_abusive_return'].mean():.2%} (n={len(first_orders)})")
