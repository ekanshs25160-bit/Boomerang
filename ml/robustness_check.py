import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, average_precision_score, precision_recall_curve
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_robustness_check():
    print("Loading data and model...")
    df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'synthetic_returns_data.csv'))
    
    with open(os.path.join(BASE_DIR, 'models', 'model_artifacts.pkl'), 'rb') as f:
        artifacts = pickle.load(f)
    
    groups = df['customer_id']
    X = df.drop(columns=['is_abusive_return', 'customer_type_DEBUG_ONLY', 'order_id', 'customer_id', 'address_id', 'payment_method_id'])
    y = df['is_abusive_return']
    
    categorical_cols = ['item_category', 'payment_method_type']
    numerical_cols = [col for col in X.columns if col not in categorical_cols]
    
    seeds = [0, 1, 7, 42, 99]
    COST_FP = 500
    COST_FN = 2000
    
    results = []
    
    for seed in seeds:
        print(f"Evaluating split with seed {seed}...")
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        train_idx, test_idx = next(gss.split(X, y, groups))
        
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numerical_cols),
                ('cat', OneHotEncoder(handle_unknown='ignore', drop='first'), categorical_cols)
            ]
        )
        
        model = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))
        ])
        
        model.fit(X_train, y_train)
        y_probs = model.predict_proba(X_test)[:, 1]
        
        pr_auc = average_precision_score(y_test, y_probs)
        
        precision_arr, recall_arr, thresholds = precision_recall_curve(y_test, y_probs)
        thresholds_eval = np.append(thresholds, 1.0)
        
        costs = []
        for thr in thresholds_eval:
            y_pred_thr = (y_probs >= thr).astype(int)
            fps = np.sum((y_pred_thr == 1) & (y_test == 0))
            fns = np.sum((y_pred_thr == 0) & (y_test == 1))
            total_cost = (fps * COST_FP) + (fns * COST_FN)
            costs.append(total_cost)
            
        optimal_idx = np.argmin(costs)
        optimal_threshold = thresholds_eval[optimal_idx]
        
        y_pred_opt = (y_probs >= optimal_threshold).astype(int)
        prec_opt = precision_score(y_test, y_pred_opt)
        rec_opt = recall_score(y_test, y_pred_opt)
        
        results.append({
            'Seed': seed,
            'PR_AUC': pr_auc,
            'Optimal_Threshold': optimal_threshold,
            'Precision': prec_opt,
            'Recall': rec_opt
        })
        
    df_results = pd.DataFrame(results)
    
    mean_pr_auc = df_results['PR_AUC'].mean()
    std_pr_auc = df_results['PR_AUC'].std()
    
    mean_prec = df_results['Precision'].mean()
    std_prec = df_results['Precision'].std()
    
    mean_rec = df_results['Recall'].mean()
    std_rec = df_results['Recall'].std()
    
    print(f"\n--- Aggregates across {len(seeds)} splits ---")
    print(f"PR-AUC:    {mean_pr_auc:.4f} ± {std_pr_auc:.4f}")
    print(f"Precision: {mean_prec:.4f} ± {std_prec:.4f}")
    print("\nRobustness Check Results:")
    print(df_results.to_string(index=False))
    
    out_path = os.path.join(BASE_DIR, 'data', 'robustness_results.csv')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df_results.to_csv(out_path, index=False)
    print("\nSaved detailed results to data/robustness_results.csv")
    
    # One-line verdict
    is_stable = std_pr_auc < (0.1 * mean_pr_auc)
    if is_stable:
        print(f"\nVerdict: PR-AUC is stable across splits (std dev is small relative to mean): {mean_pr_auc:.3f} ± {std_pr_auc:.3f}")
    else:
        print(f"\nVerdict: WARNING - PR-AUC variance is high across splits (std dev > 10% of mean): {mean_pr_auc:.3f} ± {std_pr_auc:.3f}. Single-split metrics may be untrustworthy.")

if __name__ == "__main__":
    run_robustness_check()
