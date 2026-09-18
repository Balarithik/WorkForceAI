import { useEffect, useState } from 'react';
import { getTasks } from '../api';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getTasks().then(res => setTasks(res.data)).catch(() => setError('Unable to load tasks.')).finally(() => setLoading(false));
  }, []);

  return (
    <div className="card">
      {error && <div className="result bad">{error}</div>}
      {loading && <div className="empty">Loading tasks...</div>}
      {!loading && tasks.length === 0 && <div className="empty">No active tasks.</div>}
      {!loading && tasks.length > 0 && <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SLA</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {tasks.map(task => (
            <tr key={task.id}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="font-medium text-gray-900">{task.title}</div>
                <div className="text-sm text-gray-500">{task.task_id}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  task.priority === 'CRITICAL' ? 'bg-red-100 text-red-800' : 
                  task.priority === 'HIGH' ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {task.priority}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800`}>
                  {task.status}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{task.sla_hours} hrs</td>
            </tr>
          ))}
        </tbody>
      </table>}
    </div>
  );
}
