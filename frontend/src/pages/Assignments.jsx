import { useEffect, useState } from 'react';
import { getAssignments } from '../api';

export default function Assignments() {
  const [assignments, setAssignments] = useState([]);

  useEffect(() => {
    getAssignments().then(res => setAssignments(res.data)).catch(console.error);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Employee</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Suitability</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success Prob</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {assignments.map(a => (
            <tr key={a.id}>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{a.task_details?.title}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{a.employee_details?.name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-indigo-600">{a.suitability_score.toFixed(1)}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{(a.success_probability * 100).toFixed(1)}%</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  a.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {a.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
