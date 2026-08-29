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

def load_and_preprocess_data(filepath='synthetic_returns_data.csv'):
    df = pd.read_csv(filepath)
    
    # Exclude the debugging column and identifiers
    groups = df['customer_id']
    X = df.drop(columns=['is_abusive_return', 'customer_type_DEBUG_ONLY', 'order_id', 'customer_id'])
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

def train_and_evaluate():
    print("Loading data...")
    X_train, X_test, y_train, y_test, preprocessor = load_and_preprocess_data()
    
    print("Training Logistic Regression model...")
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))
    ])
    
    model.fit(X_train, y_train)
    
    # Predict probabilities
    y_probs = model.predict_proba(X_test)[:, 1]
    
    # Calculate PR-AUC
    pr_auc = average_precision_score(y_test, y_probs)
    print(f"PR-AUC: {pr_auc:.4f}")
    
    # Calculate standard metrics at default threshold (0.5)
    y_pred_default = (y_probs >= 0.5).astype(int)
    print(f"Metrics at default 0.5 threshold:")
    print(f"  Precision: {precision_score(y_test, y_pred_default):.4f}")
    print(f"  Recall: {recall_score(y_test, y_pred_default):.4f}")
    print(f"  F1 Score: {f1_score(y_test, y_pred_default):.4f}")
    
    # --- PR Curve Plot ---
    precision, recall, thresholds = precision_recall_curve(y_test, y_probs)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, marker='.', label=f'Logistic Regression (PR-AUC = {pr_auc:.2f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend()
    plt.grid(True)
    plt.savefig('pr_curve.png')
    plt.close()
    print("Saved PR Curve to pr_curve.png")
    
    # --- Cost Analysis ---
    # Cost per FP (blocking a legit customer: lost margin + trust). E.g., ₹500
    # Cost per FN (fulfilling an abusive order: product loss + shipping). E.g., ₹2000
    COST_FP = 500
    COST_FN = 2000
    
    costs = []
    # threshold arrays from precision_recall_curve omit the 1.0 threshold, so we append 1.0
    thresholds_eval = np.append(thresholds, 1.0)
    
    for thr in thresholds_eval:
        y_pred_thr = (y_probs >= thr).astype(int)
        
        # False Positives: predicted abusive (1) but actually legit (0)
        fps = np.sum((y_pred_thr == 1) & (y_test == 0))
        # False Negatives: predicted legit (0) but actually abusive (1)
        fns = np.sum((y_pred_thr == 0) & (y_test == 1))
        
        total_cost = (fps * COST_FP) + (fns * COST_FN)
        costs.append(total_cost)
        
    optimal_idx = np.argmin(costs)
    optimal_threshold = thresholds_eval[optimal_idx]
    min_cost = costs[optimal_idx]
    
    print(f"\n--- Cost Analysis ---")
    print(f"Cost per FP: ₹{COST_FP}")
    print(f"Cost per FN: ₹{COST_FN}")
    print(f"Optimal Decision Threshold: {optimal_threshold:.4f}")
    print(f"Minimum Expected Total Cost on Test Set: ₹{min_cost}")
    
    # Plot cost analysis
    plt.figure(figsize=(8, 6))
    plt.plot(thresholds_eval, costs, label='Total Expected Cost')
    plt.axvline(optimal_threshold, color='r', linestyle='--', label=f'Optimal Threshold ({optimal_threshold:.2f})')
    plt.xlabel('Decision Threshold')
    plt.ylabel('Total Cost (₹)')
    plt.title('Cost Analysis: Threshold vs Total Cost')
    plt.legend()
    plt.grid(True)
    plt.savefig('cost_analysis.png')
    plt.close()
    print("Saved Cost Analysis to cost_analysis.png")
    
    # Metrics at optimal threshold
    y_pred_opt = (y_probs >= optimal_threshold).astype(int)
    print(f"\nMetrics at Optimal {optimal_threshold:.2f} threshold:")
    print(f"  Precision: {precision_score(y_test, y_pred_opt):.4f}")
    print(f"  Recall: {recall_score(y_test, y_pred_opt):.4f}")
    print(f"  F1 Score: {f1_score(y_test, y_pred_opt):.4f}")
    
    # --- Feature Importances / Explanations ---
    # Extract feature names from ColumnTransformer
    cat_features = model.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(X_train.select_dtypes(include=['object']).columns)
    num_features = X_train.select_dtypes(exclude=['object']).columns.tolist()
    feature_names = num_features + list(cat_features)
    
    coefficients = model.named_steps['classifier'].coef_[0]
    
    feat_importance = pd.DataFrame({
        'Feature': feature_names,
        'Coefficient': coefficients
    })
    
    # Sort by absolute value of coefficient
    feat_importance['Abs_Coefficient'] = feat_importance['Coefficient'].abs()
    feat_importance = feat_importance.sort_values(by='Abs_Coefficient', ascending=False)
    
    print("\n--- Top Feature Importances (Logistic Regression Coefficients) ---")
    print(feat_importance[['Feature', 'Coefficient']].head(10).to_string(index=False))
    
    # Save the pipeline and the optimal threshold for the demo app
    model_artifacts = {
        'model': model,
        'optimal_threshold': optimal_threshold,
        'feature_names': feature_names,
        'feature_importances': feat_importance
    }
    with open('model_artifacts.pkl', 'wb') as f:
        pickle.dump(model_artifacts, f)
    print("\nSaved model and artifacts to model_artifacts.pkl")

if __name__ == "__main__":
    train_and_evaluate()
