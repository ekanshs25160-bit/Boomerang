import streamlit as st
import pandas as pd
import pickle

st.set_page_config(page_title="Return-Risk Scorer Demo", page_icon="🛡️", layout="wide")

st.title("🛡️ Return-Risk Scorer Demo")
st.markdown("""
**Defense-Only System:** This tool scores the risk of return abuse prior to fulfillment. 
It does *not* take autonomous action (e.g., auto-blocking orders). It provides a signal for a human reviewer or downstream system to act upon.
""")

# Load artifacts
@st.cache_resource
def load_artifacts():
    try:
        with open('model_artifacts.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        st.error("Model artifacts not found. Please run `python train_eval.py` first.")
        return None

artifacts = load_artifacts()

if artifacts:
    model = artifacts['model']
    optimal_threshold = artifacts['optimal_threshold']
    feature_importances = artifacts['feature_importances']
    
    st.sidebar.header("Input Order Features")
    
    # Base Customer History
    st.sidebar.subheader("Customer History")
    account_age_days = st.sidebar.number_input("Account Age (Days)", min_value=1, value=300)
    total_past_orders = st.sidebar.number_input("Total Past Orders", min_value=0, value=5)
    historical_return_rate = st.sidebar.slider("Historical Return Rate", 0.0, 1.0, 0.1)
    historical_return_value_rate = st.sidebar.slider("Historical Return Value Rate", 0.0, 1.0, 0.12)
    days_since_last_return = st.sidebar.number_input("Days Since Last Return (-1 if none)", min_value=-1, value=-1)
    
    # This Order's Characteristics
    st.sidebar.subheader("Order Details")
    order_value = st.sidebar.number_input("Order Value (₹)", min_value=0, value=2500)
    item_category = st.sidebar.selectbox("Item Category", ['apparel', 'electronics', 'home', 'beauty', 'grocery'])
    quantity = st.sidebar.number_input("Quantity", min_value=1, value=1)
    is_multi_variant_order = st.sidebar.checkbox("Is Multi-Variant Order (e.g., multiple sizes of same shirt)")
    discount_pct_applied = st.sidebar.selectbox("Discount Applied (%)", [0, 10, 20, 30])
    
    # Address/Identity Signals
    st.sidebar.subheader("Identity & Address")
    shipping_billing_mismatch = st.sidebar.checkbox("Shipping & Billing Address Mismatch")
    is_new_shipping_address = st.sidebar.checkbox("Is New Shipping Address")
    address_reuse_across_accounts = st.sidebar.checkbox("Address Reused Across Accounts")
    
    # Payment Signals
    st.sidebar.subheader("Payment Details")
    payment_method_type = st.sidebar.selectbox("Payment Method", ['prepaid', 'COD'])
    is_new_payment_method = st.sidebar.checkbox("Is New Payment Method")
    payment_method_reuse_across_accounts = st.sidebar.checkbox("Payment Method Reused Across Accounts")
    
    # Velocity Signals
    st.sidebar.subheader("Velocity")
    orders_in_last_24h = st.sidebar.number_input("Orders in Last 24h", min_value=0, value=0)
    orders_in_last_24h_same_address = st.sidebar.number_input("Orders in Last 24h to Same Address", min_value=0, value=0)
    
    if st.sidebar.button("Score Order"):
        # Construct DataFrame
        input_data = pd.DataFrame([{
            'account_age_days': account_age_days,
            'total_past_orders': total_past_orders,
            'historical_return_rate': historical_return_rate,
            'historical_return_value_rate': historical_return_value_rate,
            'days_since_last_return': days_since_last_return,
            'order_value': order_value,
            'item_category': item_category,
            'quantity': quantity,
            'is_multi_variant_order': int(is_multi_variant_order),
            'discount_pct_applied': discount_pct_applied,
            'shipping_billing_mismatch': int(shipping_billing_mismatch),
            'is_new_shipping_address': int(is_new_shipping_address),
            'address_reuse_across_accounts': int(address_reuse_across_accounts),
            'payment_method_type': payment_method_type,
            'is_new_payment_method': int(is_new_payment_method),
            'payment_method_reuse_across_accounts': int(payment_method_reuse_across_accounts),
            'orders_in_last_24h': orders_in_last_24h,
            'orders_in_last_24h_same_address': orders_in_last_24h_same_address
        }])
        
        # Predict probability
        score_prob = model.predict_proba(input_data)[0, 1]
        score_pct = score_prob * 100
        is_flagged = score_prob >= optimal_threshold
        
        # Determine Top Factors for THIS specific order
        # We multiply the standardized/encoded feature values by the LR coefficients
        # First, transform the input
        transformed_features = model.named_steps['preprocessor'].transform(input_data)
        coefficients = model.named_steps['classifier'].coef_[0]
        
        # Calculate feature contributions for this specific prediction
        contributions = transformed_features[0] * coefficients
        feature_names = artifacts['feature_names']
        
        contrib_df = pd.DataFrame({
            'Feature': feature_names,
            'Contribution': contributions
        })
        # Sort by highest positive contribution to the risk score
        top_factors = contrib_df.sort_values(by='Contribution', ascending=False).head(3)
        
        # UI Presentation
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Risk Score", f"{score_pct:.1f}%", delta=f"{'FLAGGED' if is_flagged else 'CLEAR'}", delta_color="inverse")
            st.write(f"Decision Threshold: {optimal_threshold*100:.1f}%")
        
        with col2:
            st.markdown("### Top Contributing Risk Factors")
            if score_prob < 0.05:
                st.success("This order appears very safe. No significant risk factors detected.")
            else:
                for idx, row in top_factors.iterrows():
                    feat = row['Feature']
                    # Make names human readable
                    feat_clean = feat.replace('_', ' ').title()
                    if feat.startswith('item_category_'):
                        feat_clean = f"Item Category: {feat.replace('item_category_', '').title()}"
                    elif feat.startswith('payment_method_type_'):
                        feat_clean = f"Payment Method: {feat.replace('payment_method_type_', '').upper()}"
                    
                    st.warning(f"**{feat_clean}**")
