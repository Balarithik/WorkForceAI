import { useEffect, useState } from 'react';
import { getDecisions } from '../api';

export default function DecisionHistory() {
  const [decisions, setDecisions] = useState([]);

  useEffect(() => {
    getDecisions().then((res) => setDecisions(res.data)).catch(() => setDecisions([]));
  }, []);

  return (
    <div className="card">
      <h2>Decision Replay</h2>
      {decisions.length === 0 ? <div className="empty">No allocation decisions have been recorded yet.</div> : (
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th>Task</th>
              <th>Employee</th>
              <th>Score</th>
              <th>Reason</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map((decision) => (
              <tr key={decision.id}>
                <td>{decision.task_title || decision.task_id || 'Task'}</td>
                <td>{decision.employee_name || decision.employee || 'Unassigned'}</td>
                <td>{decision.score ?? 'N/A'}</td>
                <td>{decision.reason || 'No explanation available.'}</td>
                <td>{decision.created_at ? new Date(decision.created_at).toLocaleString() : 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
