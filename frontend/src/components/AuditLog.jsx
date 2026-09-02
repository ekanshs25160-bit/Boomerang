import React, { useState, useEffect } from 'react';

const AuditLog = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/audit-log')
      .then(res => res.json())
      .then(data => {
        // Flatten the decisions
        const flatDecisions = [];
        data.forEach(run => {
          if (run.decisions) {
            run.decisions.forEach(d => {
              flatDecisions.push({
                ...d,
                run_timestamp: run.timestamp,
                model_used: run.model_used
              });
            });
          }
        });
        setLogs(flatDecisions);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="w-full h-full bg-surface p-8 overflow-y-auto">
      <h2 className="font-display-lg text-display-lg text-on-surface mb-6">Audit Log</h2>
      <div className="bg-surface-container-lowest border border-outline-variant rounded overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline-variant">
              <th className="p-4 font-label-md text-label-md text-on-surface-variant uppercase">Order ID</th>
              <th className="p-4 font-label-md text-label-md text-on-surface-variant uppercase">Scanned At</th>
              <th className="p-4 font-label-md text-label-md text-on-surface-variant uppercase">Risk Score</th>
              <th className="p-4 font-label-md text-label-md text-on-surface-variant uppercase">Flagged</th>
              <th className="p-4 font-label-md text-label-md text-on-surface-variant uppercase">Human Action</th>
              <th className="p-4 font-label-md text-label-md text-on-surface-variant uppercase">Action Time</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="p-8 text-center text-on-surface-variant">Loading...</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan="6" className="p-8 text-center text-on-surface-variant">No audit logs found.</td></tr>
            ) : (
              logs.map(log => (
                <tr key={log.decision_id} className="border-b border-outline-variant hover:bg-surface-container-low transition-colors">
                  <td className="p-4 font-body-md text-on-surface">#{log.order_id}</td>
                  <td className="p-4 font-body-md text-on-surface">{new Date(log.run_timestamp).toLocaleString()}</td>
                  <td className="p-4 font-body-md text-on-surface">{Math.round(log.risk_score * 100)} / 100</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded font-label-sm text-label-sm ${log.flagged ? 'bg-error/10 text-error border border-error' : 'bg-green-500/10 text-green-700 border border-green-500'}`}>
                      {log.flagged ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td className="p-4 font-body-md text-on-surface capitalize">{log.human_action || '-'}</td>
                  <td className="p-4 font-body-md text-on-surface">{log.action_timestamp ? new Date(log.action_timestamp).toLocaleString() : '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditLog;
