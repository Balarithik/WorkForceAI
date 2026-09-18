import { useEffect, useState } from 'react';
import { getSlaRisks } from '../api';

export default function SlaRisk() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSlaRisks().then((res) => setItems(res.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="card empty">Loading SLA risk data...</div>;

  return (
    <div className="card">
      <h2>SLA Risk</h2>
      {items.length === 0 ? <div className="empty">No active SLA risks.</div> : (
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th>Task</th>
              <th>Priority</th>
              <th>Deadline</th>
              <th>SLA Probability</th>
              <th>Risk</th>
              <th>Assigned Employee</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.task_id}>
                <td>{item.task_id}</td>
                <td>{item.priority}</td>
                <td>{item.deadline ? new Date(item.deadline).toLocaleString() : 'N/A'}</td>
                <td>{((item.sla_probability || 0) * 100).toFixed(0)}%</td>
                <td><span className={`pill ${item.sla_risk_level === 'LOW' ? 'on' : item.sla_risk_level === 'MEDIUM' ? 'warn' : 'off'}`}>{item.sla_risk_level}</span></td>
                <td>{item.employee ? item.employee.name : 'Unassigned'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
