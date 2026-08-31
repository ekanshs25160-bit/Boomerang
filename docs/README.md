# Boomerang — Return-Risk Scorer

> **Razorpay Buildathon · AI Risk Manager Track**
> A defense-focused ML system that scores e-commerce orders for return abuse risk *before* fulfillment — giving merchants an early signal to review suspicious orders rather than shipping and absorbing the loss.

---

## What it does

Online merchants lose real money to return abuse every day:
- A **serial returner** orders 20 items over 6 months, returns 16 of them.
- A **wardrober** buys an expensive dress, wears it to an event, returns it.
- A **bracketer** orders 5 sizes of the same shirt, keeps one, returns four — costing the merchant four shipping round-trips.
- A **return ring** uses 10 fake accounts with shared addresses and COD payments to drain a merchant systematically.

This system catches these patterns *at order time* — before a single item ships — by scoring each order from 0–100% risk and surfacing the top reasons.

> **Defense-only:** The system never takes autonomous action. It outputs a risk signal for a human reviewer or downstream system to act on. It does not auto-block or auto-deny orders.

---

## What it detects (and what it doesn't)

**Detects (pre-fulfillment signals):**
| Abuse Pattern | Key Signals Used |
|---|---|
| Serial returning | High historical return rate, high order volume, recent returns |
| Wardrobing | High-value apparel + shipping/billing mismatch + elevated return value rate |
| Bracketing | Multi-variant order + apparel + high quantity |
| Return rings | Address/payment reuse across accounts, COD + high same-address velocity, new accounts |

**Does NOT detect:**
- Claims-based fraud ("item not received", "item not as described") — these require post-fulfillment data
- Stolen card fraud / payment fraud — different signal set, different model
- First-time abusers with no prior history — no historical features to leverage

---

## Project structure

```
.
├── generate_data.py        # Synthetic dataset generator (10k orders, 5 customer archetypes)
├── train_eval.py           # Model training, evaluation, cost analysis
├── demo.py                 # Streamlit demo interface
├── synthetic_returns_data.csv  # Generated dataset (auto-created)
├── model_artifacts.pkl     # Trained model + threshold (auto-created)
├── pr_curve.png            # Precision-Recall curve (auto-created)
└── cost_analysis.png       # Threshold cost sweep chart (auto-created)
```

---

## Quickstart

### 1. Install dependencies

```bash
pip3 install pandas numpy scikit-learn matplotlib streamlit networkx xgboost flask
```

### 2. Generate data

```bash
python3 ml/generate_data.py
```

Produces `synthetic_returns_data.csv` in the `data/` folder.

### 3. Train and evaluate

```bash
python3 ml/train_eval.py
```

Trains models, finds optimal thresholds, and saves to `models/` and `docs/`.

### 4. Optional: Robustness & Ring Detection

```bash
python3 ml/robustness_check.py
python3 ml/ring_detector.py
```

### 5. Run the Backend & Frontend

Start the backend:
```bash
python3 backend/app.py
```

In a separate terminal, start the React frontend:
```bash
cd frontend
npm run dev
```

---

## Model & evaluation

**Algorithm:** Logistic Regression with `class_weight='balanced'` (chosen for interpretability — coefficients are directly explainable).

**Train/test split:** Customer-level 80/20 split using `GroupShuffleSplit`. Every order for a given customer lands entirely in train or entirely in test — this correctly measures generalization to *new* customers, not just new orders from seen customers.

**Metrics (held-out test set):**

| Metric | Value |
|---|---|
| PR-AUC | ~0.53 |
| Precision (optimal threshold) | ~0.42 |
| Recall (optimal threshold) | ~0.82 |
| F1 (optimal threshold) | ~0.55 |

> **Why not accuracy?** With ~10% positive class, a model that predicts "never abusive" scores 90% accuracy. Precision-Recall AUC is the right metric for imbalanced classification.

**Cost analysis:** The decision threshold is selected by sweeping 0.01–0.99 and minimizing:

```
Total Cost = (False Positives × ₹500) + (False Negatives × ₹2000)
```

Where ₹500 = estimated cost of blocking a legitimate customer (lost margin + goodwill) and ₹2000 = estimated cost of fulfilling an abusive return (product + two-way shipping + processing). These are configurable in `train_eval.py`.

**Top features by model coefficient:**
1. `historical_return_value_rate` — how much of order value (not just count) has been returned historically
2. `address_reuse_across_accounts` — ring/burner signal
3. `is_multi_variant_order` — bracketing signal
4. `payment_method_reuse_across_accounts` — ring signal
5. `item_category` (grocery/electronics = lower risk, apparel = higher risk)

---

## Synthetic data methodology

The dataset is not random noise — it simulates a realistic customer population:

| Type | % of customers | Behavior |
|---|---|---|
| `normal` | 86% | Occasional returns, balanced order history |
| `serial_returner` | 5% | High order volume, consistently high return rate, returns every 1–2 weeks |
| `wardrober` | 4% | High-value apparel orders, return value rate far exceeds return count rate, billing mismatches |
| `bracketer` | 3% | Multi-variant apparel orders, high quantity per order |
| `ring_member` | 2% | New accounts, COD, high velocity, address & payment reuse across accounts |

Labels are assigned **probabilistically** per order based on feature combinations — not deterministically by type. Even serial returners don't flag every order, and normal customers occasionally look risky. A hidden `customer_type_DEBUG_ONLY` column allows sanity-checking the model's learned patterns against ground truth archetypes.

All features are **knowable at order time** — no post-fulfillment data (e.g., whether a return was actually filed) is used as a feature.

---

## Limitations & honest caveats

- **Synthetic data:** The model was trained on generated data, not real merchant transactions. Real-world performance will differ. Treat this as a proof-of-concept, not a production system.
- **No post-fulfillment detection:** Claim-based abuse (fake "item not received") cannot be caught with pre-fulfillment signals alone.
- **Cold start:** New customers with no order history lack historical features — the model falls back to order-level signals only, which are weaker.
- **Static model:** Return abuse patterns evolve. A production system needs periodic retraining and drift monitoring.
- **No auth, no DB, no infra:** The demo is a thin local prototype — not hardened for production deployment.
