import React, { useState, useEffect } from 'react';

const RingDetailView = ({ ringId, onBack }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hoveredNode, setHoveredNode] = useState(null);

  useEffect(() => {
    fetchRingDetail();
  }, [ringId]);

  const fetchRingDetail = async () => {
    try {
      const response = await fetch(`/api/rings/${ringId}`);
      if (!response.ok) throw new Error('Failed to fetch ring details');
      const json = await response.json();
      setData(json);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-on-surface-variant font-body-md w-full h-full flex items-center justify-center">Loading graph map...</div>;
  if (!data || data.error) return <div className="p-8 text-error font-body-md">Failed to load: {data?.error || 'Unknown error'}</div>;

  const { summary_stats, dynamic_chips, graph_data } = data;
  const { accounts, entities, links } = graph_data;

  // Compute graph height based on accounts count (80px per account + padding)
  const svgHeight = Math.max(accounts.length * 80 + 40, 200);

  const getRiskColor = (level) => {
    switch(level) {
      case 'high': return 'text-error';
      case 'medium': return 'text-yellow-600';
      default: return 'text-green-600';
    }
  };

  const getRiskBg = (level) => {
    switch(level) {
      case 'high': return 'bg-error';
      case 'medium': return 'bg-yellow-500';
      default: return 'bg-green-500';
    }
  };

  return (
    <div className="w-full h-full bg-surface p-8 overflow-y-auto pb-24">
      {/* Header Section */}
      <div className="flex items-center gap-2 mb-4 text-on-surface-variant font-label-sm uppercase tracking-wide">
        <button onClick={onBack} className="hover:text-primary transition-colors hover:underline">Dashboard</button>
        <span>/</span>
        <button onClick={onBack} className="hover:text-primary transition-colors hover:underline">Abuse Rings</button>
        <span>/</span>
        <span className="text-on-surface font-bold truncate max-w-[200px]">{ringId}</span>
      </div>

      <header className="flex justify-between items-start mb-8 pb-6 border-b border-outline-variant">
        <div>
          <h2 className="font-display-lg text-display-lg text-on-surface flex items-center gap-4 font-mono">
            {ringId}
            <span className="px-2 py-1 rounded bg-surface-container-high text-on-surface text-[12px] uppercase font-bold tracking-wider align-middle font-sans">
              {summary_stats.status}
            </span>
          </h2>
          
          <div className="flex items-center gap-6 mt-4">
            <div className="flex items-center gap-3">
              <span className={`font-label-md uppercase tracking-wider font-bold ${getRiskColor(summary_stats.risk_level)}`}>
                {summary_stats.risk_level} Risk
              </span>
              <div className="w-24 h-2 bg-surface-container-highest rounded overflow-hidden">
                <div className={`h-full ${getRiskBg(summary_stats.risk_level)}`} style={{ width: `${Math.min(summary_stats.group_abuse_rate * 100, 100)}%` }}></div>
              </div>
              <span className="font-body-sm text-on-surface-variant">{(summary_stats.group_abuse_rate * 100).toFixed(0)}% abuse rate</span>
            </div>
            
            <div className="h-6 border-l border-outline-variant"></div>
            
            <div className="flex gap-4">
               <div className="flex items-center gap-2 px-3 py-1 bg-surface-container-low rounded-full border border-outline-variant">
                  <span className="material-symbols-outlined text-sm text-on-surface-variant">group</span>
                  <span className="font-label-sm text-on-surface">{summary_stats.total_accounts} Accounts</span>
               </div>
               <div className="flex items-center gap-2 px-3 py-1 bg-surface-container-low rounded-full border border-outline-variant">
                  <span className="material-symbols-outlined text-sm text-on-surface-variant">hub</span>
                  <span className="font-label-sm text-on-surface">{summary_stats.shared_entities} Shared Entity</span>
               </div>
            </div>
          </div>
        </div>
        <button className="px-6 py-2 bg-primary text-on-primary rounded font-label-md text-label-md hover:opacity-90 transition-opacity shadow-sm">
          Start Reviewing
        </button>
      </header>

      {/* Why this was flagged */}
      <section className="mb-12">
        <h3 className="font-label-lg text-on-surface-variant uppercase mb-4 tracking-wider">Why this was flagged</h3>
        <div className="flex gap-3 flex-wrap">
          {dynamic_chips.map((chip, idx) => (
            <div key={idx} className="px-4 py-2 bg-surface-container text-on-surface rounded-full font-body-md border border-outline-variant shadow-sm text-sm">
              {chip}
            </div>
          ))}
          {dynamic_chips.length === 0 && (
             <div className="px-4 py-2 text-on-surface-variant italic font-body-md text-sm">
               No specific flags generated.
             </div>
          )}
        </div>
      </section>

      {/* Connection Map */}
      <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-8 shadow-sm">
        <header className="mb-8">
          <h3 className="font-display-md text-on-surface">Connection Map</h3>
          <p className="font-body-md text-on-surface-variant mt-1">Hover over any account or entity to highlight its direct links.</p>
        </header>

        <div className="w-full overflow-x-auto overflow-y-hidden">
          <svg 
            viewBox={`0 0 800 ${svgHeight}`} 
            className="w-full h-auto min-w-[700px] max-w-5xl mx-auto"
            style={{ minHeight: '300px' }}
          >
            {/* Draw Paths */}
            {links.map((link, i) => {
              const startY = 40 + accounts.findIndex(a => a.id === link.source) * 80;
              const endY = svgHeight / 2;
              
              const isSourceHovered = hoveredNode === link.source;
              const isTargetHovered = hoveredNode === link.target;
              const isAnyHovered = hoveredNode !== null;
              
              const isActiveLink = isSourceHovered || isTargetHovered;
              const isHighlighted = !isAnyHovered || isActiveLink;
              
              const opacity = isHighlighted ? (isActiveLink ? 1 : 0.4) : 0.1;
              const stroke = isActiveLink ? '#4f46e5' : '#cbd5e1'; 
              
              return (
                <path 
                  key={`link-${i}`}
                  d={`M 300 ${startY} C 420 ${startY}, 380 ${endY}, 500 ${endY}`}
                  stroke={stroke}
                  strokeWidth={isActiveLink ? 3 : 2}
                  fill="none"
                  style={{ opacity, transition: 'all 0.3s ease' }}
                />
              );
            })}

            {/* Draw Accounts (Left Column) */}
            <text x="150" y="20" textAnchor="middle" className="font-label-sm uppercase tracking-widest" fill="#64748b">Ring Accounts</text>
            {accounts.map((acc, i) => {
              const y = 40 + i * 80;
              
              const isHovered = hoveredNode === acc.id;
              const isLinkedToHovered = hoveredNode !== null && links.some(l => l.source === acc.id && l.target === hoveredNode);
              const isHighlighted = hoveredNode === null || isHovered || isLinkedToHovered;
              
              const opacity = isHighlighted ? 1 : 0.2;
              
              return (
                <foreignObject 
                  key={acc.id} 
                  x="0" 
                  y={y - 30} 
                  width="300" 
                  height="60" 
                  style={{ opacity, transition: 'all 0.3s ease' }}
                  onMouseEnter={() => setHoveredNode(acc.id)} 
                  onMouseLeave={() => setHoveredNode(null)}
                >
                  <div className={`h-full w-full bg-surface border ${isHovered ? 'border-primary shadow-md ring-1 ring-primary' : 'border-outline-variant shadow-sm'} rounded p-3 flex items-center gap-4 cursor-pointer transition-all`}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isHovered ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-on-surface-variant'}`}>
                      <span className="material-symbols-outlined text-lg">person</span>
                    </div>
                    <div>
                      <p className="font-label-md text-on-surface">Account {acc.id.substring(0,8)}</p>
                      <p className="font-mono text-[11px] text-on-surface-variant tracking-tight">{acc.id}</p>
                    </div>
                  </div>
                </foreignObject>
              );
            })}

            {/* Draw Entities (Right Column) */}
            <text x="640" y="20" textAnchor="middle" className="font-label-sm uppercase tracking-widest" fill="#64748b">Reused Identifiers</text>
            {entities.map((ent, i) => {
              const y = svgHeight / 2;
              
              const isHovered = hoveredNode === ent.id;
              const isLinkedToHovered = hoveredNode !== null && links.some(l => l.target === ent.id && l.source === hoveredNode);
              const isHighlighted = hoveredNode === null || isHovered || isLinkedToHovered;
              
              const opacity = isHighlighted ? 1 : 0.3;
              
              return (
                <foreignObject 
                  key={ent.id} 
                  x="500" 
                  y={y - 60} 
                  width="280" 
                  height="120" 
                  style={{ opacity, transition: 'all 0.3s ease' }}
                  onMouseEnter={() => setHoveredNode(ent.id)} 
                  onMouseLeave={() => setHoveredNode(null)}
                >
                  <div className={`h-full w-full bg-tertiary-container border ${isHovered ? 'border-tertiary shadow-lg ring-1 ring-tertiary' : 'border-tertiary/20 shadow-md'} rounded-xl p-5 flex flex-col items-center justify-center cursor-pointer text-center transition-all`}>
                    <span className="material-symbols-outlined text-on-tertiary-container text-3xl mb-2">
                      {ent.type === 'Address' ? 'home_pin' : 'credit_card'}
                    </span>
                    <p className="font-label-sm uppercase tracking-widest text-on-tertiary-container/80 mb-1">Shared {ent.type}</p>
                    <p className="font-mono text-sm text-on-tertiary-container break-all">{ent.id}</p>
                  </div>
                </foreignObject>
              );
            })}
          </svg>
        </div>
      </section>
    </div>
  );
};

export default RingDetailView;
