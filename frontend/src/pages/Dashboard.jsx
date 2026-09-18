import { useEffect, useState } from 'react';
import { getDashboardStats } from '../api';
import { Users, CheckCircle, AlertTriangle, Briefcase, Activity } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getDashboardStats().then((res) => setStats(res.data)).catch(() => setError('Unable to load dashboard data.'));
  }, []);

  if (error) return <div className="card result bad">{error}</div>;
  if (!stats) return <div className="card empty">Loading dashboard...</div>;

  const cards = [
    { title: 'Total Employees', value: stats.total_employees, icon: Users, color: 'bg-blue-500' },
    { title: 'Available Employees', value: stats.available_employees, icon: CheckCircle, color: 'bg-green-500' },
    { title: 'Active Tasks', value: stats.active_tasks, icon: Briefcase, color: 'bg-indigo-500' },
    { title: 'Critical Tasks', value: stats.critical_tasks, icon: AlertTriangle, color: 'bg-red-500' },
    { title: 'Average Workload', value: `${stats.average_workload}%`, icon: Activity, color: 'bg-blue-500' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {cards.map((card, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 border border-gray-100 flex items-center">
            <div className={`p-3 rounded-full ${card.color} text-white mr-4`}>
              <card.icon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">{card.title}</p>
              <p className="text-2xl font-bold text-gray-900">{card.value}</p>
            </div>
          </div>
        ))}
      </div>
      
      <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Welcome to WorkForceAI</h3>
        <p className="text-gray-600">
          Use the Create Task menu to submit new work requirements and leverage the AI optimization 
          engine to automatically allocate tasks to the most suitable available employees based on 
          skills, SLA probabilities, and current workloads.
        </p>
      </div>
    </div>
  );
}
