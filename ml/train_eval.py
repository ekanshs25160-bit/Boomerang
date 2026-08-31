import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score, precision_recall_curve
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import pickle
import sys
import os
from xgboost import XGBClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_and_preprocess_data(filepath=os.path.join(BASE_DIR, 'data', 'synthetic_returns_data.csv')):
    df = pd.read_csv(filepath)
    
    # Exclude the debugging column and identifiers
    groups = df['customer_id']
    X = df.drop(columns=['is_abusive_return', 'customer_type_DEBUG_ONLY', 'order_id', 'customer_id', 'address_id', 'payment_method_id'])
    y = df['is_abusive_return']
    
    # Identify categorical and numerical columns
    categorical_cols = ['item_category', 'payment_method_type']
    numerical_cols = [col for col in X.columns if col not in categorical_cols]
    
    # Create preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', drop='first'), categorical_cols)
        ]
    )
    
    # Split the data (80/20 by customer)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))
    
    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]
    
    return X_train, X_test, y_train, y_test, preprocessor

def evaluate_model(y_test, y_probs, model_name, cost_fp, cost_fn):
    pr_auc = average_precision_score(y_test, y_probs)
    print(f"{model_name} -> PR-AUC: {pr_auc:.4f}")
    
    # Cost analysis
    precision, recall, thresholds = precision_recall_curve(y_test, y_probs)
    thresholds_eval = np.append(thresholds, 1.0)
    costs = []
    
    for thr in thresholds_eval:
        y_pred_thr = (y_probs >= thr).astype(int)
        fps = np.sum((y_pred_thr == 1) & (y_test == 0))
        fns = np.sum((y_pred_thr == 0) & (y_test == 1))
        total_cost = (fps * cost_fp) + (fns * cost_fn)
        costs.append(total_cost)
        
    optimal_idx = np.argmin(costs)
    optimal_threshold = thresholds_eval[optimal_idx]
    min_cost = costs[optimal_idx]
    
    y_pred_opt = (y_probs >= optimal_threshold).astype(int)
    prec_opt = precision_score(y_test, y_pred_opt)
    rec_opt = recall_score(y_test, y_pred_opt)
    f1_opt = f1_score(y_test, y_pred_opt)
    
    print(f"\n--- Cost Analysis ({model_name}) ---")
    print(f"Optimal Decision Threshold: {optimal_threshold:.4f}")
    print(f"Minimum Expected Total Cost: ₹{min_cost}")
    print(f"Metrics at Optimal Threshold:")
    print(f"  Precision: {prec_opt:.4f}")
    print(f"  Recall: {rec_opt:.4f}")
    print(f"  F1 Score: {f1_opt:.4f}")
    
    return {
        'pr_auc': pr_auc,
        'precision': precision,
        'recall': recall,
        'thresholds_eval': thresholds_eval,
        'costs': costs,
        'optimal_threshold': optimal_threshold,
        'min_cost': min_cost,
        'prec_opt': prec_opt,
        'rec_opt': rec_opt,
        'f1_opt': f1_opt
    }

def train_and_evaluate():
    print("Loading data...")
    X_train, X_test, y_train, y_test, preprocessor_lr = load_and_preprocess_data()
    
    categorical_cols = ['item_category', 'payment_method_type']
    numerical_cols = [col for col in X_train.columns if col not in categorical_cols]
    
    # 1. Logistic Regression
    print("\n--- Training Logistic Regression model ---")
    model_lr = Pipeline(steps=[
        ('preprocessor', preprocessor_lr),
        ('classifier', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))
    ])
    model_lr.fit(X_train, y_train)
    y_probs_lr = model_lr.predict_proba(X_test)[:, 1]
    
    # 2. XGBoost
    print("\n--- Training XGBoost model ---")
    preprocessor_xgb = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', drop='first'), categorical_cols)
        ],
        remainder='passthrough'
    )
    scale_pos_weight = np.sum(y_train == 0) / np.sum(y_train == 1)
    model_xgb = Pipeline(steps=[
        ('preprocessor', preprocessor_xgb),
        ('classifier', XGBClassifier(scale_pos_weight=scale_pos_weight, random_state=42, use_label_encoder=False, eval_metric='logloss'))
    ])
    model_xgb.fit(X_train, y_train)
    y_probs_xgb = model_xgb.predict_proba(X_test)[:, 1]
    
    # Evaluate
    COST_FP = 500
    COST_FN = 2000
    
    print("\n=== Evaluation Results ===")
    res_lr = evaluate_model(y_test, y_probs_lr, "Logistic Regression", COST_FP, COST_FN)
    res_xgb = evaluate_model(y_test, y_probs_xgb, "XGBoost", COST_FP, COST_FN)
    
    # Side-by-side comparison
    print("\n=== Side-by-Side Comparison ===")
    comp_df = pd.DataFrame({
        'Model': ['Logistic Regression', 'XGBoost'],
        'PR-AUC': [res_lr['pr_auc'], res_xgb['pr_auc']],
        'Opt Threshold': [res_lr['optimal_threshold'], res_xgb['optimal_threshold']],
        'Precision': [res_lr['prec_opt'], res_xgb['prec_opt']],
        'Recall': [res_lr['rec_opt'], res_xgb['rec_opt']],
        'F1 Score': [res_lr['f1_opt'], res_xgb['f1_opt']],
        'Min Expected Cost (₹)': [res_lr['min_cost'], res_xgb['min_cost']]
    })
    print(comp_df.to_string(index=False))
    
    # Plot PR Curve Comparison
    plt.figure(figsize=(8, 6))
    plt.plot(res_lr['recall'], res_lr['precision'], label=f"LR (PR-AUC = {res_lr['pr_auc']:.3f})")
    plt.plot(res_xgb['recall'], res_xgb['precision'], label=f"XGB (PR-AUC = {res_xgb['pr_auc']:.3f})")
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve Comparison')
    plt.legend()
    plt.grid(True)
    out_path = os.path.join(BASE_DIR, 'docs', 'pr_curve_comparison.png')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path)
    plt.close()
    print("\nSaved PR Curve Comparison to pr_curve_comparison.png")

    # Plot original PR Curve just for LR to not break old behavior expectations
    plt.figure(figsize=(8, 6))
    plt.plot(res_lr['recall'], res_lr['precision'], marker='.', label=f"Logistic Regression (PR-AUC = {res_lr['pr_auc']:.2f})")
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend()
    plt.grid(True)
    out_path = os.path.join(BASE_DIR, 'docs', 'pr_curve.png')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path)
    plt.close()
    print("Saved Original PR Curve (LR) to pr_curve.png")
    
    # Plot original Cost Analysis (LR)
    plt.figure(figsize=(8, 6))
    plt.plot(res_lr['thresholds_eval'], res_lr['costs'], label='Total Expected Cost (LR)')
    plt.axvline(res_lr['optimal_threshold'], color='r', linestyle='--', label=f"Optimal Threshold ({res_lr['optimal_threshold']:.2f})")
    plt.xlabel('Decision Threshold')
    plt.ylabel('Total Cost (₹)')
    plt.title('Cost Analysis: Threshold vs Total Cost')
    plt.legend()
    plt.grid(True)
    out_path = os.path.join(BASE_DIR, 'docs', 'cost_analysis.png')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path)
    plt.close()
    print("Saved Original Cost Analysis to cost_analysis.png")
    
    # Feature Importances - Logistic Regression
    cat_features_lr = model_lr.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(categorical_cols)
    feature_names_lr = numerical_cols + list(cat_features_lr)
    coef_lr = model_lr.named_steps['classifier'].coef_[0]
    
    feat_imp_lr = pd.DataFrame({
        'Feature': feature_names_lr,
        'Coefficient': coef_lr
    })
    feat_imp_lr['Abs_Coefficient'] = feat_imp_lr['Coefficient'].abs()
    feat_imp_lr = feat_imp_lr.sort_values(by='Abs_Coefficient', ascending=False)
    
    print("\n--- Top Feature Importances (Logistic Regression) ---")
    print(feat_imp_lr[['Feature', 'Coefficient']].head(10).to_string(index=False))
    
    # Feature Importances - XGBoost
    cat_features_xgb = model_xgb.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(categorical_cols)
    feature_names_xgb = list(cat_features_xgb) + numerical_cols
    imp_xgb = model_xgb.named_steps['classifier'].feature_importances_
    
    feat_imp_xgb = pd.DataFrame({
        'Feature': feature_names_xgb,
        'Importance (Gain)': imp_xgb
    })
    feat_imp_xgb = feat_imp_xgb.sort_values(by='Importance (Gain)', ascending=False)
    
    print("\n--- Top Feature Importances (XGBoost) ---")
    print(feat_imp_xgb.head(10).to_string(index=False))
    
    # Save artifacts
    model_artifacts = {
        'logistic_regression': {
            'model': model_lr,
            'optimal_threshold': res_lr['optimal_threshold'],
            'feature_names': feature_names_lr,
            'feature_importances': feat_imp_lr
        },
        'xgboost': {
            'model': model_xgb,
            'optimal_threshold': res_xgb['optimal_threshold'],
            'feature_names': feature_names_xgb,
            'feature_importances': feat_imp_xgb
        }
    }
    out_path = os.path.join(BASE_DIR, 'models', 'model_artifacts.pkl')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        pickle.dump(model_artifacts, f)
    print("\nSaved model artifacts (both models) to model_artifacts.pkl")

if __name__ == "__main__":
    train_and_evaluate()