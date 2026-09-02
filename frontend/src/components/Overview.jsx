import React, { useState, useEffect } from 'react';

const Overview = ({ onTabChange }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/overview')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-8 text-on-surface-variant font-body-md">Loading overview...</div>;
  }

  if (!stats || stats.error) {
    return <div className="p-8 text-error font-body-md">Failed to load overview data.</div>;
  }

  const { total_accounts, total_transactions, total_scored, flagged_count, risk_distribution, queue_status } = stats;
  
  const maxRisk = Math.max(risk_distribution.low, risk_distribution.medium, risk_distribution.high, 1);

  return (
    <div className="w-full h-full bg-surface p-8 overflow-y-auto">
      <header className="mb-8">
        <h2 className="font-display-lg text-display-lg text-on-surface">Investigation overview</h2>
        <p className="font-body-md text-on-surface-variant mt-1">Aggregate statistics for the most recent detection run</p>
      </header>

      {flagged_count > 0 && (
        <div className="bg-error/10 border border-error rounded p-4 mb-8 flex justify-between items-center">
          <div className="flex items-center gap-3 text-error">
            <span className="material-symbols-outlined">warning</span>
            <span className="font-label-lg font-bold">{flagged_count} high-risk cases need attention</span>
          </div>
          <button 
            onClick={() => onTabChange('queue')}
            className="px-4 py-2 bg-error text-on-error rounded font-label-md hover:opacity-90 transition-opacity"
          >
            Review Queue
          </button>
        </div>
      )}

      {/* Run Summary */}
      <h3 className="font-label-lg text-label-lg text-on-surface-variant uppercase mb-4 tracking-wider">Run Summary</h3>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-6">
          <p className="font-label-sm text-on-surface-variant mb-1 uppercase">Accounts</p>
          <p className="font-display-md text-on-surface">{total_accounts}</p>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-6">
          <p className="font-label-sm text-on-surface-variant mb-1 uppercase">Transactions</p>
          <p className="font-display-md text-on-surface">{total_transactions}</p>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-6">
          <p className="font-label-sm text-on-surface-variant mb-1 uppercase">Scored</p>
          <p className="font-display-md text-on-surface">{total_scored}</p>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-6">
          <p className="font-label-sm text-on-surface-variant mb-1 uppercase">Flagged</p>
          <p className="font-display-md text-error font-bold">{flagged_count}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-20">
        {/* Risk Distribution */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-6">
          <h3 className="font-label-lg text-label-lg text-on-surface-variant uppercase mb-6 tracking-wider">Risk Distribution</h3>
          
          <div className="mb-5">
            <div className="flex justify-between font-label-sm mb-2">
              <span className="text-green-600 font-bold uppercase tracking-wide">Low Risk</span>
              <span className="text-on-surface font-bold">{risk_distribution.low}</span>
            </div>
            <div className="w-full bg-surface-container-high rounded-full h-3 overflow-hidden">
              <div className="bg-green-500 h-full rounded-full" style={{ width: `${(risk_distribution.low / maxRisk) * 100}%` }}></div>
            </div>
          </div>
          
          <div className="mb-5">
            <div className="flex justify-between font-label-sm mb-2">
              <span className="text-yellow-600 font-bold uppercase tracking-wide">Medium Risk</span>
              <span className="text-on-surface font-bold">{risk_distribution.medium}</span>
            </div>
            <div className="w-full bg-surface-container-high rounded-full h-3 overflow-hidden">
              <div className="bg-yellow-500 h-full rounded-full" style={{ width: `${(risk_distribution.medium / maxRisk) * 100}%` }}></div>
            </div>
          </div>
          
          <div className="mb-2">
            <div className="flex justify-between font-label-sm mb-2">
              <span className="text-error font-bold uppercase tracking-wide">High Risk</span>
              <span className="text-on-surface font-bold">{risk_distribution.high}</span>
            </div>
            <div className="w-full bg-surface-container-high rounded-full h-3 overflow-hidden">
              <div className="bg-error h-full rounded-full" style={{ width: `${(risk_distribution.high / maxRisk) * 100}%` }}></div>
            </div>
          </div>
        </div>

        {/* Queue Status */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded p-6">
          <h3 className="font-label-lg text-label-lg text-on-surface-variant uppercase mb-6 tracking-wider">Queue Status</h3>
          <div className="space-y-3">
            <div 
              onClick={() => onTabChange('queue')}
              className="flex justify-between items-center p-3 rounded bg-surface-container-low hover:bg-surface-container-high transition-colors cursor-pointer border border-transparent hover:border-outline-variant"
            >
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary">inbox</span>
                <span className="font-body-md text-on-surface">New / Unreviewed</span>
              </div>
              <span className="font-label-md bg-primary-container text-on-primary-container px-2 py-0.5 rounded">{queue_status.new}</span>
            </div>
            
            <div className="flex justify-between items-center p-3 rounded border border-transparent">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-on-surface-variant">hourglass_empty</span>
                <span className="font-body-md text-on-surface">Reviewing</span>
              </div>
              <span className="font-label-md text-on-surface-variant">{queue_status.reviewing}</span>
            </div>
            
            <div className="flex justify-between items-center p-3 rounded border border-transparent">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-green-600">check_circle</span>
                <span className="font-body-md text-on-surface">Approved</span>
              </div>
              <span className="font-label-md text-on-surface-variant">{queue_status.approved}</span>
            </div>
            
            <div className="flex justify-between items-center p-3 rounded border border-transparent">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-error">cancel</span>
                <span className="font-body-md text-on-surface">Declined</span>
              </div>
              <span className="font-label-md text-on-surface-variant">{queue_status.declined}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
