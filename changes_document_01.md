# Boomerang — Return Risk Scoring System: Changes Document

## Overview

The project implements a **Return-Risk Scorer** — a machine-learning pipeline designed to identify potentially abusive return orders in an e-commerce context. The system is defensive-only: it scores risk and surfaces signals for human review, without auto-blocking orders.

---

## Files Added / Changed

### 1. [`generate_data.py`](file:///Users/ekanshshrotriya/Documents/Boomerang/generate_data.py)
**Purpose:** Synthetic dataset generator for training and evaluation.

#### Key decisions & changes:
- **Customer archetypes modelled** — Five realistic customer types are simulated with distinct statistical profiles:
  | Type | Behavior |
  |------|----------|
  | `normal` (86%) | Low return rate, standard orders |
  | `serial_returner` (5%) | High historical return rate (Beta 5,2), recent returns |
  | `wardrober` (4%) | High-value apparel orders, shipping/billing mismatch, inflated return value rate |
  | `bracketer` (3%) | High quantity apparel, multi-variant orders |
  | `ring_member` (2%) | New accounts, address/payment reuse across accounts, COD, high velocity |

- **Feature engineering** — 18 behavioral and transactional features are generated covering:
  - Customer history (`account_age_days`, `total_past_orders`, `historical_return_rate`, `historical_return_value_rate`, `days_since_last_return`)
  - Order characteristics (`order_value`, `item_category`, `quantity`, `is_multi_variant_order`, `discount_pct_applied`)
  - Identity/address signals (`shipping_billing_mismatch`, `is_new_shipping_address`, `address_reuse_across_accounts`)
  - Payment signals (`payment_method_type`, `is_new_payment_method`, `payment_method_reuse_across_accounts`)
  - Velocity signals (`orders_in_last_24h`, `orders_in_last_24h_same_address`)

- **Probabilistic label generation** — Rather than deterministic labels, a `risk_score` is accumulated from rule-based signal weights and used as a probability for `np.random.binomial`, making the dataset realistic and noisy.

- **`customer_type_DEBUG_ONLY` column** — Intentionally included to allow sanity-checking fraud rates per archetype; excluded from model training.

---

### 2. [`train_eval.py`](file:///Users/ekanshshrotriya/Documents/Boomerang/train_eval.py)
**Purpose:** Model training, evaluation, and artifact serialization.

#### Key decisions & changes:
- **Customer-level train/test split** — Uses `GroupShuffleSplit` on `customer_id` to prevent data leakage (same customer cannot appear in both train and test sets). Standard `train_test_split` was deliberately avoided.

- **Preprocessing pipeline** — A `sklearn.pipeline.Pipeline` combines:
  - `StandardScaler` for numerical features
  - `OneHotEncoder` (drop-first) for categorical features (`item_category`, `payment_method_type`)

- **Model choice** — `LogisticRegression` with `class_weight='balanced'` to handle class imbalance; trained for up to 1000 iterations.

- **Evaluation metrics:**
  - PR-AUC (primary metric — appropriate for imbalanced data)
  - Precision, Recall, F1 at default 0.5 threshold
  - Precision, Recall, F1 at cost-optimal threshold

- **Cost-aware threshold optimization** — A custom cost function sweeps all PR-curve thresholds to find the optimal decision boundary:
  - False Positive cost: ₹500 (blocking a legitimate customer — lost margin + trust)
  - False Negative cost: ₹2000 (fulfilling an abusive order — product loss + shipping)
  - The threshold minimising total cost is selected and persisted.

- **Visualizations saved:**
  - [`pr_curve.png`](file:///Users/ekanshshrotriya/Documents/Boomerang/pr_curve.png) — Precision-Recall curve
  - [`cost_analysis.png`](file:///Users/ekanshshrotriya/Documents/Boomerang/cost_analysis.png) — Threshold vs Total Cost plot with optimal threshold marked

- **Feature importance reporting** — Top-10 features ranked by absolute logistic regression coefficient are printed to console.

- **Artifact serialization** — Model pipeline, optimal threshold, feature names, and feature importances are pickled to [`model_artifacts.pkl`](file:///Users/ekanshshrotriya/Documents/Boomerang/model_artifacts.pkl) for use by the demo app.

---

### 3. [`demo.py`](file:///Users/ekanshshrotriya/Documents/Boomerang/demo.py)
**Purpose:** Interactive Streamlit demo for real-time order risk scoring.

#### Key decisions & changes:
- **Streamlit UI** — Sidebar-driven form with grouped inputs matching the training feature set:
  - Customer History
  - Order Details
  - Identity & Address
  - Payment Details
  - Velocity

- **Artifact loading with caching** — `@st.cache_resource` is used to load the pickled model artifacts once per session. Graceful error message shown if `model_artifacts.pkl` is missing.

- **Real-time risk scoring:**
  - Constructs a single-row `pd.DataFrame` from sidebar inputs
  - Calls `model.predict_proba()` and converts to a percentage score
  - Compares against the cost-optimal threshold from training to determine FLAGGED vs CLEAR

- **Explainability panel** — For each scored order, the top 3 contributing risk factors are surfaced by:
  - Transforming the input through the preprocessing step
  - Multiplying transformed values by logistic regression coefficients
  - Sorting by highest positive contribution

- **Human-readable feature labels** — Raw feature names (e.g., `item_category_electronics`) are cleaned and reformatted for display (e.g., `Item Category: Electronics`).

- **UI layout:** Two-column layout — risk score metric (left) + top contributing factors (right).

---

### 4. [`synthetic_returns_data.csv`](file:///Users/ekanshshrotriya/Documents/Boomerang/synthetic_returns_data.csv)
**Purpose:** Pre-generated dataset (10,000 order records) committed alongside code so the model can be trained without running `generate_data.py` separately.

---

### 5. [`model_artifacts.pkl`](file:///Users/ekanshshrotriya/Documents/Boomerang/model_artifacts.pkl)
**Purpose:** Pre-trained model artifacts committed alongside code so `demo.py` can run immediately without needing to execute `train_eval.py`.

Contains:
- Trained sklearn `Pipeline` (preprocessor + logistic regression classifier)
- Cost-optimal decision threshold
- Feature names list
- Feature importances DataFrame

---

### 6. [`pr_curve.png`](file:///Users/ekanshshrotriya/Documents/Boomerang/pr_curve.png) & [`cost_analysis.png`](file:///Users/ekanshshrotriya/Documents/Boomerang/cost_analysis.png)
**Purpose:** Evaluation outputs committed for quick reference without re-running training.

---

## Architecture Summary

```
generate_data.py
    └── synthetic_returns_data.csv (10k orders, 5 customer archetypes)

train_eval.py
    ├── reads  synthetic_returns_data.csv
    ├── trains LogisticRegression (customer-level split, balanced weights)
    ├── outputs pr_curve.png, cost_analysis.png
    └── writes model_artifacts.pkl

demo.py
    ├── loads  model_artifacts.pkl
    └── Streamlit UI → score any order in real time
```

---

## Design Principles Applied

| Principle | Implementation |
|-----------|---------------|
| No auto-blocking | Scores are advisory; system surfaces risk, not decisions |
| No data leakage | `GroupShuffleSplit` on `customer_id` |
| Imbalance handling | `class_weight='balanced'` + PR-AUC as primary metric |
| Business-aligned threshold | Cost function uses ₹500 FP / ₹2000 FN |
| Explainability | Per-order feature contribution breakdown in UI |
| Reproducibility | `np.random.seed(42)`, `random_state=42` throughout |
