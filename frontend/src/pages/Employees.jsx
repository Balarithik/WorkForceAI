import { useEffect, useState } from 'react';
import { getEmployees, updateEmployee } from '../api';

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchEmployees = () => {
    setLoading(true);
    getEmployees().then(res => setEmployees(res.data)).catch(() => setError('Unable to load employees.')).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const toggleAvailability = async (emp) => {
    const newStatus = emp.availability === 'AVAILABLE' ? 'UNAVAILABLE' : 'AVAILABLE';
    try {
      await updateEmployee(emp.id, { availability: newStatus });
      fetchEmployees();
    } catch (e) {
      console.error(e);
      setError(e.response?.data?.detail || e.response?.data?.error || 'Unable to update employee status.');
    }
  };

  return (
    <div className="card">
      <div className="sub" style={{ marginBottom: 14 }}>Live data &bull; SQLite</div>
      {error && <div className="result bad">{error}</div>}
      {loading && <div className="empty">Loading employees...</div>}
      {!loading && employees.length === 0 && <div className="empty">No employees found.</div>}
      {!loading && employees.length > 0 && <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Employee</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Team</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Manager</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Shift</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Workload</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Availability</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Certifications</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {employees.map(emp => (
            <tr key={emp.id}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="font-medium text-gray-900">{emp.name}</div>
                <div className="text-sm text-gray-500">{emp.employee_id}</div>
                <div className="text-xs text-gray-400">{emp.email || 'No email'}</div>
                <div className="text-xs text-gray-400">{emp.phone_number || 'No phone'}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.job_title || emp.department}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.team || emp.department}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.manager_name || 'Unassigned'}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.preferred_shift || 'DAY'}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.current_workload_percent}%</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  emp.availability === 'AVAILABLE' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {emp.availability}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {Array.isArray(emp.certifications) && emp.certifications.length > 0 ? emp.certifications.join(', ') : 'None'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button 
                  onClick={() => toggleAvailability(emp)}
                  className="text-indigo-600 hover:text-indigo-900 bg-indigo-50 px-3 py-1 rounded"
                >
                  Toggle Status
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>}
    </div>
  );
}
