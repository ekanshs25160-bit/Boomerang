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
                # Gather shared entities for report
                shared_entities = set()
                for u in comp:
                    for v in comp:
                        if u != v and G.has_edge(u, v):
                            shared_entities.add(f"{G[u][v]['type']} ({G[u][v]['shared_id']})")
                            
                suspected_rings.append({
                    'members': list(comp),
                    'size': len(comp),
                    'group_abuse_rate': group_abuse_rate,
                    'shared_entities': list(shared_entities)
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
        print(f"  Size: {ring['size']} accounts")
        print(f"  Group Abuse Rate: {ring['group_abuse_rate']:.2%}")
        print(f"  Shared Entities: {', '.join(ring['shared_entities'])}")
        print(f"  Members: {', '.join(ring['members'])}")
        
        total_implicated += ring['size']
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

if __name__ == '__main__':
    main()
