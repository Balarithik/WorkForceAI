import { useEffect, useState } from 'react';
import { getEmployees, updateEmployee } from '../api';

export default function Employees() {
  const [employees, setEmployees] = useState([]);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = () => {
    getEmployees().then(res => setEmployees(res.data)).catch(console.error);
  };

  const toggleAvailability = async (emp) => {
    const newStatus = emp.availability === 'AVAILABLE' ? 'UNAVAILABLE' : 'AVAILABLE';
    try {
      await updateEmployee(emp.id, { availability: newStatus });
      fetchEmployees();
    } catch (e) {
      console.error(e);
      alert('Failed to update employee status');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Employee</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Workload</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Availability</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {employees.map(emp => (
            <tr key={emp.id}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="font-medium text-gray-900">{emp.name}</div>
                <div className="text-sm text-gray-500">{emp.employee_id}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.department}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.current_workload_percent}%</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  emp.availability === 'AVAILABLE' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {emp.availability}
                </span>
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
      </table>
    </div>
  );
}
