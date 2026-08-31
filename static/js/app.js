let currentOrders = [];
let selectedOrderId = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchOrders();
});

async function fetchOrders() {
    try {
        const response = await fetch('/api/orders');
        currentOrders = await response.json();
        
        document.getElementById('queue-count').textContent = `${currentOrders.length} Items`;
        renderQueue();
    } catch (error) {
        console.error('Error fetching orders:', error);
        document.getElementById('order-queue').innerHTML = '<div class="text-center text-error py-8">Failed to load orders.</div>';
    }
}

function renderQueue() {
    const queueContainer = document.getElementById('order-queue');
    queueContainer.innerHTML = '';
    
    currentOrders.forEach(order => {
        const isHighRisk = order.risk_score >= order.threshold;
        
        const item = document.createElement('div');
        item.className = `bg-surface-container-lowest border p-4 rounded cursor-pointer relative overflow-hidden shadow-sm transition-colors group ${selectedOrderId === order.order_id ? 'ring-1 ring-primary-fixed border-primary' : 'border-outline-variant hover:border-outline'}`;
        item.onclick = () => selectOrder(order.order_id);
        
        item.innerHTML = `
            ${isHighRisk ? '<div class="absolute left-0 top-0 bottom-0 w-1 bg-error"></div>' : '<div class="absolute left-0 top-0 bottom-0 w-1 bg-green-500"></div>'}
            <div class="flex justify-between items-start mb-2 pl-2">
                <span class="font-label-md text-label-md text-on-surface ${selectedOrderId !== order.order_id ? 'group-hover:text-primary transition-colors' : ''}">#${order.order_id}</span>
                <div class="${isHighRisk ? 'bg-error/10 text-error border-error' : 'bg-green-500/10 text-green-700 border-green-500'} font-label-sm text-label-sm px-2 py-1 rounded border-l">
                    ${isHighRisk ? 'High' : 'Low'}
                </div>
            </div>
            <div class="flex justify-between items-end mt-4 pl-2">
                <span class="font-body-md text-body-md text-on-surface-variant">${order.customer_id.substring(0,8)}...</span>
                <span class="font-headline-sm text-headline-sm text-on-surface">$${order.order_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
            </div>
        `;
        queueContainer.appendChild(item);
    });
}

function selectOrder(orderId) {
    selectedOrderId = orderId;
    renderQueue(); // Update selection styling
    
    const order = currentOrders.find(o => o.order_id === orderId);
    if (!order) return;
    
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('detail-view').style.display = 'flex';
    
    // Header
    document.getElementById('detail-order-id').textContent = `#${order.order_id}`;
    document.getElementById('detail-customer-id').textContent = order.customer_id;
    document.getElementById('detail-order-value').textContent = `$${order.order_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    // Risk Score
    const scorePct = Math.round(order.risk_score * 100);
    const isHighRisk = order.risk_score >= order.threshold;
    
    document.getElementById('risk-score-text').textContent = scorePct;
    
    const riskCircle = document.getElementById('risk-circle');
    const dashArray = 251.2;
    const dashOffset = dashArray - (dashArray * scorePct / 100);
    
    // Slight delay to allow CSS transition
    setTimeout(() => {
        riskCircle.style.strokeDashoffset = dashOffset;
        riskCircle.setAttribute('class', isHighRisk ? 'text-error' : 'text-green-500');
    }, 50);
    
    const badge = document.getElementById('risk-badge');
    badge.textContent = isHighRisk ? 'High Risk' : 'Low Risk';
    badge.className = `${isHighRisk ? 'bg-error/10 text-error border-error' : 'bg-green-500/10 text-green-700 border-green-500'} font-label-sm text-label-sm px-3 py-1 rounded border-l-2 uppercase tracking-widest mt-2`;
    
    // Top Factors
    const factorsList = document.getElementById('risk-factors-list');
    if (scorePct < 5 || order.top_factors.length === 0) {
        factorsList.innerHTML = '<li class="p-3 text-on-surface-variant">No significant risk factors detected. Order looks safe.</li>';
    } else {
        factorsList.innerHTML = order.top_factors.map(factor => `
            <li class="flex items-start gap-3 p-3 bg-surface-container-low rounded border border-outline-variant/50">
                <span class="material-symbols-outlined text-error mt-0.5">warning</span>
                <div>
                    <p class="font-label-md text-label-md text-on-surface mb-1">${factor.feature}</p>
                    <p class="font-body-md text-body-md text-on-surface-variant text-sm">Impact: +${factor.contribution.toFixed(2)} | Value: ${factor.value}</p>
                </div>
            </li>
        `).join('');
    }
    
    // Snapshot
    document.getElementById('snapshot-age').textContent = `${order.account_age_days} days`;
    document.getElementById('snapshot-past-orders').textContent = order.total_past_orders;
    document.getElementById('snapshot-return-rate').textContent = `${(order.historical_return_rate * 100).toFixed(1)}%`;
    document.getElementById('snapshot-orders-24h').textContent = order.orders_in_last_24h;
}
