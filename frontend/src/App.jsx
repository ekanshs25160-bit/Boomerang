import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import OrderQueue from './components/OrderQueue';
import OrderDetail from './components/OrderDetail';
import Toast from './components/Toast';

function App() {
  const [orders, setOrders] = useState([]);
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await fetch('/api/orders');
      if (!response.ok) throw new Error('Failed to fetch orders');
      const data = await response.json();
      setOrders(data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError('Failed to load orders.');
      setLoading(false);
    }
  };

  const showToast = (message, type = 'success') => {
    setToastMessage({ message, type, id: Date.now() });
    setTimeout(() => setToastMessage(null), 3000);
  };

  const removeAndSelectNext = () => {
    setOrders((prevOrders) => {
      const idx = prevOrders.findIndex(o => o.order_id === selectedOrderId);
      if (idx === -1) return prevOrders;
      
      const newOrders = [...prevOrders];
      newOrders.splice(idx, 1);
      
      if (newOrders.length > 0) {
        const nextIdx = Math.min(idx, newOrders.length - 1);
        setSelectedOrderId(newOrders[nextIdx].order_id);
      } else {
        setSelectedOrderId(null);
      }
      
      return newOrders;
    });
  };

  const handleAction = async (actionType) => {
    if (!selectedOrderId) return;
    
    // Map the actionType from UI to DB schema
    let dbAction = actionType;
    if (actionType === 'requestInfo') dbAction = 'info_requested';
    if (actionType === 'approve') dbAction = 'approved';
    if (actionType === 'decline') dbAction = 'declined';
    
    try {
      const response = await fetch(`/api/orders/${selectedOrderId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action: dbAction }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to record action');
      }
      
      if (actionType === 'approve') {
        showToast(`Order #${selectedOrderId} approved`, 'success');
        removeAndSelectNext();
      } else if (actionType === 'decline') {
        showToast(`Order #${selectedOrderId} declined — flagged as high risk`, 'error');
        removeAndSelectNext();
      } else if (actionType === 'requestInfo') {
        showToast(`Info request sent to customer for order #${selectedOrderId}`, 'success');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to record action. Please try again.', 'error');
    }
  };

  const selectedOrder = orders.find(o => o.order_id === selectedOrderId) || null;

  return (
    <div className="flex h-full w-full">
      <Sidebar />
      <main className="ml-sidebar-width mt-16 h-[calc(100vh-64px)] flex w-[calc(100%-280px)]">
        <OrderQueue 
          orders={orders} 
          loading={loading} 
          error={error} 
          selectedOrderId={selectedOrderId} 
          onSelectOrder={setSelectedOrderId} 
        />
        <OrderDetail 
          order={selectedOrder} 
          onAction={handleAction} 
        />
      </main>
      
      {toastMessage && (
        <Toast 
          message={toastMessage.message} 
          type={toastMessage.type} 
          key={toastMessage.id} 
        />
      )}
    </div>
  );
}

export default App;
