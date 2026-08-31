import React, { useEffect, useState } from 'react';

const RiskGauge = ({ scorePct, isHighRisk }) => {
  const dashArray = 251.2;
  const [dashOffset, setDashOffset] = useState(dashArray);
  
  useEffect(() => {
    // Animate after mount
    setTimeout(() => {
      setDashOffset(dashArray - (dashArray * scorePct / 100));
    }, 50);
  }, [scorePct]);

  return (
    <div className="relative w-32 h-32 mb-4">
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        <circle className="text-surface-container-high" cx="50" cy="50" fill="transparent" r="40" stroke="currentColor" strokeWidth="8"></circle>
        <circle 
          className={isHighRisk ? 'text-error' : 'text-green-500'} 
          cx="50" cy="50" fill="transparent" r="40" 
          stroke="currentColor" 
          strokeDasharray={dashArray} 
          strokeDashoffset={dashOffset} 
          strokeLinecap="round" strokeWidth="8"
          style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
        ></circle>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-headline-md text-headline-md text-on-surface">{scorePct}</span>
        <span className="font-label-sm text-label-sm text-on-surface-variant">/100</span>
      </div>
    </div>
  );
};

export default RiskGauge;
