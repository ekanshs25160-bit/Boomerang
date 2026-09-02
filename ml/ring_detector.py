import pandas as pd
import networkx as nx
import os

def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Loading data from synthetic_returns_data.csv...")
    df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'synthetic_returns_data.csv'))
    overall_abuse_rate = df['is_abusive_return'].mean()

    # Customer level stats
    cust_stats = df.groupby('customer_id').agg({
        'is_abusive_return': 'mean',
        'customer_type_DEBUG_ONLY': 'first'
    }).reset_index()

    G = nx.Graph()
    for _, row in cust_stats.iterrows():
        G.add_node(row['customer_id'], 
                   abuse_rate=row['is_abusive_return'], 
                   ctype=row['customer_type_DEBUG_ONLY'])

    print("Building graph of shared entities...")
    
    # Build edges from shared addresses
    address_groups = df[df['address_reuse_across_accounts'] == 1].groupby('address_id')['customer_id'].unique()
    for addr, custs in address_groups.items():
        if len(custs) > 1:
            for i in range(len(custs)):
                for j in range(i+1, len(custs)):
                    G.add_edge(custs[i], custs[j], type='address', shared_id=addr)

    # Build edges from shared payment methods
    payment_groups = df[df['payment_method_reuse_across_accounts'] == 1].groupby('payment_method_id')['customer_id'].unique()
    for pay, custs in payment_groups.items():
        if len(custs) > 1:
            for i in range(len(custs)):
                for j in range(i+1, len(custs)):
                    G.add_edge(custs[i], custs[j], type='payment', shared_id=pay)

    print("Finding connected components...")
    components = list(nx.connected_components(G))
    suspected_rings = []
    
    for comp in components:
        if len(comp) >= 3:
            comp_abuse_rates = [G.nodes[n]['abuse_rate'] for n in comp]
            group_abuse_rate = sum(comp_abuse_rates) / len(comp)
            
            # A ring is suspected if its group abuse rate is 1.5x the population baseline
            if group_abuse_rate > overall_abuse_rate * 1.5:
                shared_entity_type = "unknown"
                shared_entity_id = "unknown"
                for u in comp:
                    for v in comp:
                        if u != v and G.has_edge(u, v):
                            shared_entity_type = 'address' if G[u][v]['type'] == 'address' else 'payment_method'
                            shared_entity_id = G[u][v]['shared_id']
                            break
                    if shared_entity_type != "unknown":
                        break
                        
                comp_df = df[df['customer_id'].isin(comp)]
                cod_pct = (comp_df['payment_method_type'] == 'COD').mean()
                
                dynamic_chips = []
                if group_abuse_rate > 0.5:
                    dynamic_chips.append(f"Cluster exhibits severe serial-returning behavior ({int(group_abuse_rate * 100)}% average).")
                if cod_pct > 0.6:
                    dynamic_chips.append(f"Sudden spike in Cash-on-Delivery (COD) orders ({int(cod_pct * 100)}% of cluster).")
                if shared_entity_type == 'address':
                    dynamic_chips.append("Multiple accounts funneling orders to 1 shared delivery destination(s).")
                elif shared_entity_type == 'payment_method':
                    dynamic_chips.append(f"Identical payment instruments used across {len(comp)} isolated accounts.")
                        
                import uuid
                ring_id = f"ring_{uuid.uuid4().hex[:8]}"
                risk_level = "high" if group_abuse_rate >= 0.6 else ("medium" if group_abuse_rate >= 0.3 else "low")
                
                suspected_rings.append({
                    'ring_id': ring_id,
                    'member_count': len(comp),
                    'shared_entity_type': shared_entity_type,
                    'shared_entity_id': shared_entity_id,
                    'group_abuse_rate': group_abuse_rate,
                    'risk_level': risk_level,
                    'members': list(comp),
                    'dynamic_chips': dynamic_chips
                })
    
    print("\n" + "="*80)
    print("RING DETECTION REPORT")
    print("="*80)
    print(f"Population Baseline Abuse Rate: {overall_abuse_rate:.2%}")
    print(f"Detected {len(suspected_rings)} suspected rings (criteria: size >= 3, abuse rate > {overall_abuse_rate * 1.5:.2%})")
    print("-" * 80)
    
    total_implicated = 0
    caught_true_ring_members = 0
    
    for i, ring in enumerate(suspected_rings, 1):
        print(f"Ring #{i}:")
        print(f"  Size: {ring['member_count']} accounts")
        print(f"  Group Abuse Rate: {ring['group_abuse_rate']:.2%}")
        print(f"  Shared Entities: {ring['shared_entity_type']} ({ring['shared_entity_id']})")
        print(f"  Members: {', '.join(ring['members'])}")
        
        total_implicated += ring['member_count']
        for member in ring['members']:
            if G.nodes[member]['ctype'] == 'ring_member':
                caught_true_ring_members += 1
        print()
        
    # Ground truth evaluation
    true_ring_members_total = len(cust_stats[cust_stats['customer_type_DEBUG_ONLY'] == 'ring_member'])
    
    print("=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total rings detected: {len(suspected_rings)}")
    print(f"Total accounts implicated: {total_implicated}")
    print(f"True 'ring_member' accounts in population: {true_ring_members_total}")
    
    if true_ring_members_total > 0:
        recall = caught_true_ring_members / true_ring_members_total
        print(f"Recall (fraction of true ring members caught): {recall:.2%} ({caught_true_ring_members}/{true_ring_members_total})")
    
    if total_implicated > 0:
        precision = caught_true_ring_members / total_implicated
        print(f"Precision (fraction of flagged accounts that are true ring members): {precision:.2%} ({caught_true_ring_members}/{total_implicated})")
    print("=" * 80)
    
    if suspected_rings:
        import sys
        sys.path.append(BASE_DIR)
        from backend import db
        print(f"\nPersisting {len(suspected_rings)} rings to database...")
        db.record_detected_rings(suspected_rings)
        print("Done.")

if __name__ == '__main__':
    main()
