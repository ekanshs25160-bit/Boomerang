import React from 'react';

const OrderDetail = ({ order, onAction }) => {
  if (!order) {
    return (
      <div className="flex-1 h-full flex flex-col items-center justify-center bg-background">
        <span className="material-symbols-outlined text-outline-variant" style={{ fontSize: '64px' }}>inbox</span>
        <h2 className="font-headline-sm text-headline-sm text-on-surface mt-4">Select an order</h2>
        <p className="text-on-surface-variant text-sm mt-2">Click on an order from the queue to view its risk analysis.</p>
      </div>
    );
  }

  const scorePct = Math.round(order.risk_score * 100);
  
  let riskLevel = 'Low Risk';
  let riskCircleClass = 'text-green-500';
  let riskBadgeClass = 'bg-green-500/10 text-green-700 border-green-500';

  if (order.risk_score >= 0.55) {
    riskLevel = 'High Risk';
    riskCircleClass = 'text-error';
    riskBadgeClass = 'bg-error/10 text-error border-error';
  } else if (order.risk_score >= 0.35) {
    riskLevel = 'Medium Risk';
    riskCircleClass = 'text-yellow-500';
    riskBadgeClass = 'bg-yellow-500/10 text-yellow-700 border-yellow-500';
  }
  
  const circumference = 251.2; // 2 * Math.PI * 40
  const dashOffset = circumference - (scorePct / 100) * circumference;

  return (
    <div className="flex-1 h-full flex flex-col bg-background relative overflow-hidden">
      <div className="flex-1 overflow-y-auto p-gutter pb-32">
        {/* Header */}
        <div className="flex justify-between items-end mb-8 border-b border-outline-variant pb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="font-display-lg text-display-lg text-on-surface">#{order.order_id}</h2>
              <span className="bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm px-2 py-1 rounded">Pending</span>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">calendar_today</span> {new Date(order.created_at || Date.now()).toLocaleString()}
              <span className="mx-2 text-outline-variant">|</span>
              <span className="material-symbols-outlined text-[16px]">person</span> {order.customer_id.substring(0,8)}
            </p>
          </div>
          <div className="text-right">
            <p className="font-label-sm text-label-sm text-on-surface-variant uppercase mb-1">Total Value</p>
            <p className="font-display-lg text-display-lg text-on-surface">
              ${(order.order_value || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
            </p>
          </div>
        </div>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-12 gap-6">
          {/* Risk Score Widget */}
          <div className="col-span-12 lg:col-span-4 bg-surface-container-lowest border border-outline-variant rounded p-6 flex flex-col items-center justify-center text-center">
            <h3 className="font-label-sm text-label-sm text-on-surface-variant uppercase w-full text-left mb-6">Risk Assessment</h3>
            <div className="relative w-32 h-32 mb-4">
              {/* Circular Progress SVG */}
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle className="text-surface-container-high" cx="50" cy="50" fill="transparent" r="40" stroke="currentColor" strokeWidth="8"></circle>
                <circle className={riskCircleClass} cx="50" cy="50" fill="transparent" r="40" stroke="currentColor" strokeDasharray={circumference} strokeDashoffset={dashOffset} strokeLinecap="round" strokeWidth="8"></circle>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="font-headline-md text-headline-md text-on-surface">{scorePct}</span>
                <span className="font-label-sm text-label-sm text-on-surface-variant">/100</span>
              </div>
            </div>
            <div className={`${riskBadgeClass} font-label-sm text-label-sm px-3 py-1 rounded border-l-2 uppercase tracking-widest mt-2`}>
              {riskLevel}
            </div>
          </div>

          {/* AI Explainability Card */}
          <div className="col-span-12 lg:col-span-8 bg-surface-container-lowest border border-outline-variant rounded p-6 flex flex-col">
            <h3 className="font-label-sm text-label-sm text-on-surface-variant uppercase mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">psychology</span>
              Top Risk Factors
            </h3>
            <ul className="space-y-4 flex-1">
              {scorePct < 5 || !order.top_factors || order.top_factors.length === 0 ? (
                <li className="p-3 text-on-surface-variant">No significant risk factors detected. Order looks safe.</li>
              ) : (
                order.top_factors.map((factor, idx) => {
                  const impact = factor.impact ?? factor.contribution;
                  let iconColor = 'text-green-500';
                  let iconName = 'check_circle';
                  if (factor.severity === 'high' || impact > 0.5) {
                    iconColor = 'text-error';
                    iconName = 'warning';
                  } else if (factor.severity === 'medium' || impact > 0.2) {
                    iconColor = 'text-yellow-600';
                    iconName = 'info';
                  }
                  
                  return (
                    <li key={idx} className="flex items-start gap-3 p-3 bg-surface-container-low rounded border border-outline-variant/50">
                      <span className={`material-symbols-outlined ${iconColor} mt-0.5`}>
                        {iconName}
                      </span>
                      <div>
                        <p className="font-label-md text-label-md text-on-surface mb-1">{factor.name || factor.feature}</p>
                        <p className="font-body-md text-body-md text-on-surface-variant text-sm">
                          Impact: +{impact.toFixed(2)} | Value: {factor.value}
                        </p>
                      </div>
                    </li>
                  );
                })
              )}
            </ul>
          </div>

          {/* Customer Snapshot Card */}
          <div className="col-span-12 bg-surface-container-lowest border border-outline-variant rounded p-6">
            <h3 className="font-label-sm text-label-sm text-on-surface-variant uppercase mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">account_box</span>
              Customer Profile
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Account Age</p>
                <p className="font-headline-sm text-headline-sm text-on-surface">{(order.customer_profile?.account_age_days ?? order.account_age_days)} days</p>
              </div>
              <div>
                <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Past Orders</p>
                <p className="font-headline-sm text-headline-sm text-on-surface">{(order.customer_profile?.past_orders ?? order.total_past_orders)}</p>
              </div>
              <div>
                <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Hist. Return Rate</p>
                <p className="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px]">insights</span>
                  {((order.customer_profile?.historical_return_rate ?? order.historical_return_rate) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Bar (Bottom Fixed) */}
      <div className="absolute bottom-0 left-0 right-0 bg-surface-container-lowest border-t border-outline-variant p-4 px-gutter flex justify-end items-center gap-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-20">
        <button 
          onClick={() => onAction('requestInfo')}
          className="h-10 px-6 bg-surface-container-lowest text-on-surface border border-outline-variant rounded font-label-md text-label-md hover:bg-surface-container-low transition-colors"
        >
          Request Info
        </button>
        <button 
          onClick={() => onAction('approve')}
          className="h-10 px-6 bg-surface-container-lowest text-primary border border-outline-variant hover:border-primary rounded font-label-md text-label-md hover:bg-surface-container-low transition-colors"
        >
          Approve & Fulfill
        </button>
        <button 
          onClick={() => onAction('decline')}
          className="h-10 px-6 bg-error text-on-error rounded font-label-md text-label-md hover:opacity-90 transition-opacity shadow-sm flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-[18px]">block</span>
          Decline Order
        </button>
      </div>
    </div>
  );
};

export default OrderDetail;
