import React, { useState, useEffect } from 'react';
import RingDetailView from './RingDetailView';

const AbuseRings = () => {
  const [rings, setRings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [minScore, setMinScore] = useState(0);
  const [status, setStatus] = useState('New');
  const [selectedRing, setSelectedRing] = useState(null);

  useEffect(() => {
    fetchRings();
  }, [minScore, status]);

  const fetchRings = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/rings?min_score=${minScore}&status=${status}`);
      if (!response.ok) throw new Error('Failed to fetch rings');
      const data = await response.json();
      setRings(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskBg = (level) => {
    switch(level) {
      case 'high': return 'bg-error';
      case 'medium': return 'bg-yellow-500';
      default: return 'bg-green-500';
    }
  };

  if (selectedRing) {
    return <RingDetailView ringId={selectedRing.ring_id} onBack={() => setSelectedRing(null)} />;
  }

  return (
    <div className="w-full h-full bg-surface p-8 overflow-y-auto">
      <header className="mb-8">
        <h2 className="font-display-lg text-display-lg text-on-surface">Abuse rings</h2>
        <p className="font-body-md text-on-surface-variant mt-1">Investigate coordinated accounts sharing addresses or payment methods.</p>
      </header>

      <div className="flex gap-4 mb-6 items-end">
        <div>
          <label className="block font-label-sm text-on-surface-variant mb-1">Min Score (%)</label>
          <input 
            type="number" 
            className="px-3 py-2 bg-surface-container rounded border border-outline focus:border-primary outline-none text-on-surface"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value)}
            min="0"
            max="100"
          />
        </div>
        <div>
          <label className="block font-label-sm text-on-surface-variant mb-1">Status</label>
          <select 
            className="px-3 py-2 bg-surface-container rounded border border-outline focus:border-primary outline-none text-on-surface min-w-[150px]"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="All">All</option>
            <option value="New">New</option>
            <option value="Reviewing">Reviewing</option>
            <option value="Confirmed">Confirmed</option>
            <option value="Dismissed">Dismissed</option>
          </select>
        </div>
      </div>

      <div className="bg-surface-container-lowest border border-outline-variant rounded overflow-hidden mb-12">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline-variant">
              <th className="p-4 font-label-md text-on-surface-variant uppercase whitespace-nowrap">Risk Level</th>
              <th className="p-4 font-label-md text-on-surface-variant uppercase">Status</th>
              <th className="p-4 font-label-md text-on-surface-variant uppercase">Ring ID</th>
              <th className="p-4 font-label-md text-on-surface-variant uppercase">Members</th>
              <th className="p-4 font-label-md text-on-surface-variant uppercase">Shared Entity</th>
              <th className="p-4 font-label-md text-on-surface-variant uppercase">Why This Was Flagged</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {loading ? (
              <tr>
                <td colSpan="6" className="p-8 text-center text-on-surface-variant font-body-md">Loading rings...</td>
              </tr>
            ) : rings.length === 0 ? (
              <tr>
                <td colSpan="6" className="p-8 text-center text-on-surface-variant font-body-md">No abuse rings found matching criteria.</td>
              </tr>
            ) : (
              rings.map(ring => (
                <tr 
                  key={ring.ring_id} 
                  className="hover:bg-surface-container-low transition-colors cursor-pointer"
                  onClick={() => setSelectedRing(ring)}
                >
                  <td className="p-4 align-top w-32">
                    <div className="flex items-center gap-3">
                      <div className="w-16 h-2 bg-surface-container-highest rounded overflow-hidden">
                        <div className={`h-full ${getRiskBg(ring.risk_level)}`} style={{ width: `${Math.min(ring.group_abuse_rate * 100, 100)}%` }}></div>
                      </div>
                      <span className="font-label-md text-on-surface">{(ring.group_abuse_rate * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="p-4 align-top">
                    <span className="px-2 py-1 rounded bg-surface-container-high text-on-surface text-[10px] uppercase font-bold tracking-wider">
                      {ring.status}
                    </span>
                  </td>
                  <td className="p-4 align-top font-mono text-sm text-on-surface whitespace-nowrap">
                    {ring.ring_id}
                  </td>
                  <td className="p-4 align-top">
                    <div className="font-body-md text-on-surface font-bold">{ring.member_count} accounts</div>
                    <div className="font-mono text-xs text-on-surface-variant mt-1 max-w-[150px] truncate" title={ring.members.join(', ')}>
                      {ring.members.join(', ')}
                    </div>
                  </td>
                  <td className="p-4 align-top">
                    <div className="font-body-md text-on-surface">
                      {ring.shared_entity_type === 'address' ? 'Shared address' : 'Shared payment method'}
                    </div>
                    <div className="font-mono text-xs text-on-surface-variant mt-1 text-primary">
                      {ring.shared_entity_id}
                    </div>
                  </td>
                  <td className="p-4 align-top">
                    <div className="flex flex-col gap-2 items-start">
                      <span className="inline-block px-2 py-1 rounded bg-error/10 text-error text-xs font-medium border border-error/20 whitespace-nowrap">
                        {ring.shared_entity_type === 'address' ? 'Members share a physical address' : 'Members share a payment method'}
                      </span>
                      <span className="inline-block px-2 py-1 rounded bg-error/10 text-error text-xs font-medium border border-error/20 whitespace-nowrap">
                        Group abuse rate is {(ring.group_abuse_rate * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AbuseRings;
