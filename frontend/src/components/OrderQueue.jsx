import React from 'react';

const OrderQueue = ({ orders, loading, error, selectedOrderId, onSelectOrder }) => {
  return (
    <div className="w-1/3 min-w-[320px] max-w-[400px] border-r border-outline-variant bg-surface h-full flex flex-col">
      <div className="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-lowest sticky top-0 z-10">
        <h2 className="font-headline-sm text-headline-sm text-on-surface">Pending Review</h2>
        <span className="bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm px-2 py-1 rounded">
          {orders.length} Items
        </span>
      </div>
      <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-2 bg-surface-container-low">
        {loading && <div className="text-center text-outline-variant py-8">Loading orders...</div>}
        {error && <div className="text-center text-error py-8">{error}</div>}
        
        {!loading && !error && orders.map((order) => {
          const isHighRisk = order.risk_score >= order.threshold;
          const isSelected = selectedOrderId === order.order_id;
          
          return (
            <div 
              key={order.order_id}
              onClick={() => onSelectOrder(order.order_id)}
              className={`bg-surface-container-lowest border p-4 rounded cursor-pointer relative overflow-hidden transition-colors group ${isSelected ? 'ring-1 ring-primary-fixed border-outline-variant shadow-sm' : 'border-outline-variant hover:border-outline'}`}
            >
              <div className={`absolute left-0 top-0 bottom-0 w-1 ${isHighRisk ? 'bg-error' : 'bg-yellow-500'}`}></div>
              <div className="flex justify-between items-start mb-2">
                <span className={`font-label-md text-label-md text-on-surface ${!isSelected ? 'group-hover:text-primary transition-colors' : ''}`}>#{order.order_id}</span>
                <div className={`${isHighRisk ? 'bg-error/10 text-error border-error' : 'bg-yellow-500/10 text-yellow-700 border-yellow-500'} font-label-sm text-label-sm px-2 py-1 rounded border-l`}>
                  {isHighRisk ? 'High' : 'Medium'}
                </div>
              </div>
              <div className="flex justify-between items-end mt-4">
                <span className="font-body-md text-body-md text-on-surface-variant">{order.customer_id.substring(0,8)}...</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">
                  ${order.order_value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OrderQueue;
