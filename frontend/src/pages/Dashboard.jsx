import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Briefcase, CheckCircle, Users, Clock3 } from 'lucide-react';
import { getAssignments, getDashboardStats, getEmployees, getSlaRisks, getTasks } from '../api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [slaRisks, setSlaRisks] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      getDashboardStats(),
      getEmployees(),
      getTasks(),
      getAssignments(),
      getSlaRisks(),
    ])
      .then(([statsRes, employeesRes, tasksRes, assignmentsRes, slaRes]) => {
        setStats(statsRes.data);
        setEmployees(employeesRes.data || []);
        setTasks(tasksRes.data || []);
        setAssignments(assignmentsRes.data || []);
        setSlaRisks(slaRes.data || []);
      })
      .catch(() => setError('Unable to load dashboard data.'));
  }, []);

  if (error) return <div className="card result bad">{error}</div>;
  if (!stats) return <div className="card empty">Loading dashboard...</div>;

  const totalBusy = employees.filter((employee) => employee.availability === 'BUSY').length;
  const unavailable = employees.filter((employee) => employee.availability === 'UNAVAILABLE').length;
  const activeAssignments = assignments.filter((assignment) => assignment.status === 'ACTIVE');
  const pendingTasks = tasks.filter((task) => task.status === 'PENDING').length;
  const inProgressTasks = tasks.filter((task) => task.status === 'IN_PROGRESS').length;
  const completedTasks = tasks.filter((task) => task.status === 'COMPLETED').length;
  const topRiskTasks = [...slaRisks].sort((a, b) => Number(b.risk_probability || 0) - Number(a.risk_probability || 0)).slice(0, 4);

  const cards = [
    { title: 'Total Employees', value: stats.total_employees, detail: 'Across the workforce', icon: Users, tone: 'blue' },
    { title: 'Available', value: stats.available_employees, detail: 'Ready to assign', icon: CheckCircle, tone: 'green' },
    { title: 'Active Tasks', value: stats.active_tasks, detail: 'Currently tracked', icon: Briefcase, tone: 'indigo' },
    { title: 'Critical Tasks', value: stats.critical_tasks, detail: 'Needs attention', icon: AlertTriangle, tone: 'red' },
    { title: 'Average Workload', value: `${stats.average_workload}%`, detail: 'Team utilization', icon: Activity, tone: 'amber' },
  ];

  const riskMap = {
    LOW: 'Low',
    MEDIUM: 'Medium',
    HIGH: 'High',
    CRITICAL: 'Critical',
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-head">
        <div>
          <p className="eyebrow">Overview</p>
          <h2>Workforce Assignment</h2>
        </div>
        <div className="dashboard-date">{new Date().toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</div>
      </div>

      <div className="metric-grid">
        {cards.map((card, i) => (
          <div key={i} className={`metric-card metric-card--${card.tone}`}>
            <div className="metric-card__icon">
              <card.icon size={18} />
            </div>
            <div>
              <p>{card.title}</p>
              <strong>{card.value}</strong>
              <span>{card.detail}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel__header">
            <h3>Workforce overview</h3>
          </div>
          <div className="workforce-overview">
            <div className="mini-stat">
              <span>Available</span>
              <strong>{stats.available_employees}</strong>
              <div className="progress"><i style={{ width: `${Math.max((stats.available_employees / Math.max(stats.total_employees, 1)) * 100, 0)}%` }} /></div>
            </div>
            <div className="mini-stat">
              <span>Busy</span>
              <strong>{totalBusy}</strong>
              <div className="progress progress--warn"><i style={{ width: `${Math.max((totalBusy / Math.max(stats.total_employees, 1)) * 100, 0)}%` }} /></div>
            </div>
            <div className="mini-stat">
              <span>Unavailable</span>
              <strong>{unavailable}</strong>
              <div className="progress progress--error"><i style={{ width: `${Math.max((unavailable / Math.max(stats.total_employees, 1)) * 100, 0)}%` }} /></div>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <h3>Task overview</h3>
          </div>
          <div className="task-pills">
            <div className="task-pill"><span>Critical</span><strong>{tasks.filter((task) => task.priority === 'CRITICAL').length}</strong></div>
            <div className="task-pill"><span>High priority</span><strong>{tasks.filter((task) => task.priority === 'HIGH').length}</strong></div>
            <div className="task-pill"><span>Pending</span><strong>{pendingTasks}</strong></div>
            <div className="task-pill"><span>In progress</span><strong>{inProgressTasks}</strong></div>
            <div className="task-pill"><span>Completed</span><strong>{completedTasks}</strong></div>
          </div>
        </section>
      </div>

      <div className="dashboard-grid dashboard-grid--bottom">
        <section className="panel">
          <div className="panel__header">
            <h3>SLA risk</h3>
          </div>
          <div className="risk-list">
            {topRiskTasks.length === 0 ? (
              <div className="empty">No active SLA risks.</div>
            ) : (
              topRiskTasks.map((risk, index) => (
                <div className="risk-row" key={`${risk.task_id || risk.task || index}`}>
                  <div>
                    <strong>{risk.task_id || risk.task || 'Task'}</strong>
                    <small>{risk.priority || 'N/A'}</small>
                  </div>
                  <div>
                    <span>{risk.sla_remaining_hours ?? risk.sla_hours ?? '—'}h</span>
                  </div>
                  <div>
                    <span className={`risk-badge risk-badge--${String(risk.level || risk.risk_level || 'LOW').toLowerCase()}`}>
                      {riskMap[risk.level || risk.risk_level || 'LOW'] || risk.level || 'Low'}
                    </span>
                  </div>
                  <div>
                    <small>{risk.employee_name || risk.assigned_employee || 'Unassigned'}</small>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <h3>Current assignments</h3>
          </div>
          <div className="assignment-list">
            {activeAssignments.length === 0 ? (
              <div className="empty">No active assignments.</div>
            ) : (
              activeAssignments.slice(0, 5).map((assignment) => {
                const task = tasks.find((item) => item.id === assignment.task) || {};
                const employee = employees.find((item) => item.id === assignment.employee) || {};
                return (
                  <div className="assignment-row" key={assignment.id || task.task_id || 'assignment'}>
                    <div>
                      <strong>{task.title || task.task_id || 'Untitled task'}</strong>
                      <small>{task.priority || 'MEDIUM'} priority</small>
                    </div>
                    <div>
                      <span>{employee.name || 'Unassigned'}</span>
                    </div>
                    <div>
                      <small>{employee.current_workload_percent ?? 0}% workload</small>
                    </div>
                    <div>
                      <span className="status-pill">{assignment.status}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
