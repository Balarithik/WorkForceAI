import { useEffect, useMemo, useState } from 'react';
import { getAssignments, getDashboardStats, getEmployees, getSlaRisks } from '../api';
import { Activity, AlertTriangle, Briefcase, CheckCircle2, Clock3, TrendingUp, Users } from 'lucide-react';

const priorityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [slaRisks, setSlaRisks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      getDashboardStats(),
      getEmployees(),
      getAssignments(),
      getSlaRisks(),
    ])
      .then(([statsRes, employeesRes, assignmentsRes, slaRes]) => {
        setStats(statsRes.data);
        setEmployees(Array.isArray(employeesRes.data) ? employeesRes.data : []);
        setAssignments(Array.isArray(assignmentsRes.data) ? assignmentsRes.data : []);
        setSlaRisks(Array.isArray(slaRes.data) ? slaRes.data : []);
      })
      .catch(() => setError('Unable to load dashboard data.'))
      .finally(() => setLoading(false));
  }, []);

  const activeAssignments = useMemo(
    () => assignments.filter((assignment) => assignment.status === 'ACTIVE').sort((a, b) => (b.id || 0) - (a.id || 0)),
    [assignments],
  );

  const workforceOverview = useMemo(() => {
    const total = employees.length || 1;
    const available = employees.filter((employee) => employee.availability === 'AVAILABLE').length;
    const busy = employees.filter((employee) => employee.availability !== 'AVAILABLE').length;
    const unavailable = employees.filter((employee) => employee.availability === 'UNAVAILABLE').length;

    return {
      availablePct: (available / total) * 100,
      busyPct: (busy / total) * 100,
      unavailablePct: (unavailable / total) * 100,
      available,
      busy,
      unavailable,
    };
  }, [employees]);

  const topSlaRisks = useMemo(
    () => [...slaRisks].sort((a, b) => (b.sla_risk_probability || 0) - (a.sla_risk_probability || 0)).slice(0, 4),
    [slaRisks],
  );

  const taskOverview = useMemo(() => {
    const tasks = stats ? { pending: stats.unassigned_tasks || 0, assigned: activeAssignments.length, inProgress: 0, completed: 0 } : { pending: 0, assigned: 0, inProgress: 0, completed: 0 };
    return tasks;
  }, [activeAssignments.length, stats]);

  if (error) return <div className="card result bad">{error}</div>;
  if (loading || !stats) return <div className="card empty">Loading dashboard...</div>;

  const metrics = [
    { label: 'Total Employees', value: stats.total_employees, detail: 'company roster', icon: Users, tone: 'blue' },
    { label: 'Available', value: stats.available_employees, detail: 'ready to assign', icon: CheckCircle2, tone: 'green' },
    { label: 'Active Tasks', value: stats.active_tasks, detail: 'in current pipeline', icon: Briefcase, tone: 'indigo' },
    { label: 'Assigned', value: activeAssignments.length, detail: 'currently staffed', icon: TrendingUp, tone: 'violet' },
    { label: 'Waiting', value: stats.unassigned_tasks || 0, detail: 'still pending', icon: Clock3, tone: 'amber' },
    { label: 'Critical Tasks', value: stats.critical_tasks, detail: 'high priority', icon: AlertTriangle, tone: 'red' },
    { label: 'High SLA Risk', value: slaRisks.filter((item) => item.sla_risk_level === 'HIGH' || item.sla_risk_level === 'CRITICAL').length, detail: 'need review', icon: Activity, tone: 'orange' },
    { label: 'Average Workload', value: `${stats.average_workload}%`, detail: 'team utilization', icon: TrendingUp, tone: 'slate' },
  ];

  return (
    <div className="page-shell">
      <header className="page-header card">
        <div>
          <p className="eyebrow">WorkForceAI</p>
          <h2 className="page-title">Workforce Assignment</h2>
        </div>
        <div className="header-meta">
          <span className="meta-pill">Live overview</span>
          <span className="meta-time">{new Date().toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>
        </div>
      </header>

      <section className="metric-grid">
        {metrics.map(({ label, value, detail, icon: Icon, tone }) => (
          <article key={label} className="kpi-card">
            <div className={`kpi-icon ${tone}`}>
              <Icon size={18} />
            </div>
            <div className="kpi-copy">
              <p>{label}</p>
              <h3>{value}</h3>
              <span>{detail}</span>
            </div>
          </article>
        ))}
      </section>

      <div className="dashboard-grid">
        <section className="section-card">
          <div className="section-header">
            <div>
              <p className="eyebrow">Overview</p>
              <h3>Workforce Overview</h3>
            </div>
          </div>

          <div className="overview-stack">
            <div className="overview-row">
              <div className="overview-labels">
                <span>Available employees</span>
                <strong>{workforceOverview.available}</strong>
              </div>
              <div className="progress-track"><div className="progress-bar green" style={{ width: `${workforceOverview.availablePct}%` }} /></div>
            </div>
            <div className="overview-row">
              <div className="overview-labels">
                <span>Busy employees</span>
                <strong>{workforceOverview.busy}</strong>
              </div>
              <div className="progress-track"><div className="progress-bar amber" style={{ width: `${workforceOverview.busyPct}%` }} /></div>
            </div>
            <div className="overview-row">
              <div className="overview-labels">
                <span>Unavailable employees</span>
                <strong>{workforceOverview.unavailable}</strong>
              </div>
              <div className="progress-track"><div className="progress-bar red" style={{ width: `${workforceOverview.unavailablePct}%` }} /></div>
            </div>
          </div>
        </section>

        <section className="section-card">
          <div className="section-header">
            <div>
              <p className="eyebrow">Execution</p>
              <h3>Task Overview</h3>
            </div>
          </div>

          <div className="task-grid">
            <div className="task-stat">
              <span>Critical</span>
              <strong>{stats.critical_tasks}</strong>
            </div>
            <div className="task-stat">
              <span>High priority</span>
              <strong>{slaRisks.filter((item) => item.priority === 'HIGH' || item.priority === 'CRITICAL').length}</strong>
            </div>
            <div className="task-stat">
              <span>Pending</span>
              <strong>{stats.unassigned_tasks || 0}</strong>
            </div>
            <div className="task-stat">
              <span>In progress</span>
              <strong>{Math.max(stats.active_tasks - (stats.unassigned_tasks || 0), 0)}</strong>
            </div>
            <div className="task-stat">
              <span>Completed</span>
              <strong>{Math.max(assignments.filter((a) => a.status === 'COMPLETED').length, 0)}</strong>
            </div>
          </div>
        </section>
      </div>

      <div className="dashboard-grid">
        <section className="section-card">
          <div className="section-header">
            <div>
              <p className="eyebrow">Risk watch</p>
              <h3>SLA Risk</h3>
            </div>
          </div>

          <div className="list-stack">
            {topSlaRisks.length === 0 ? (
              <div className="empty-min">No active SLA risks.</div>
            ) : (
              topSlaRisks.map((item) => (
                <div key={item.task_id} className="list-row">
                  <div>
                    <div className="list-primary">{item.task_id}</div>
                    <div className="list-secondary">{item.priority} priority</div>
                  </div>
                  <div className="list-meta">
                    <span className="meta-badge">{item.sla_risk_level}</span>
                  </div>
                  <div className="list-meta right">
                    <span>{item.remaining_sla_hours ?? 0}h</span>
                    <strong>{item.employee ? item.employee.name : 'Unassigned'}</strong>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="section-card">
          <div className="section-header">
            <div>
              <p className="eyebrow">Current work</p>
              <h3>Current Assignments</h3>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Priority</th>
                  <th>Employee</th>
                  <th>Workload</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {activeAssignments.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="empty-cell">No active assignments.</td>
                  </tr>
                ) : (
                  activeAssignments.slice(0, 6).map((assignment) => {
                    const employee = assignment.employee_details || assignment.employee || null;
                    const task = assignment.task_details || assignment.task || null;
                    const priorityValue = (task?.priority || 'MEDIUM').toUpperCase();
                    const priority = priorityValue === 'CRITICAL' ? 'Critical' : priorityValue === 'HIGH' ? 'High' : priorityValue === 'LOW' ? 'Low' : 'Medium';
                    const suitability = Number(assignment.suitability_score || 0).toFixed(1);
                    const workload = employee?.current_workload_percent ?? 0;
                    return (
                      <tr key={assignment.id ?? `${task?.task_id || 'task'}-${employee?.employee_id || 'employee'}`}>
                        <td>
                          <div className="table-task">{task?.title || task?.task_id || 'Task'}</div>
                          <small>{task?.task_id || 'N/A'}</small>
                        </td>
                        <td><span className={`prio ${priorityValue === 'CRITICAL' ? 'p0' : priorityValue === 'HIGH' ? 'p1' : priorityValue === 'LOW' ? 'p3' : 'p2'}`}>{priority}</span></td>
                        <td>{employee?.name || 'Unassigned'}</td>
                        <td>{workload}%</td>
                        <td><span className="meta-badge green">{suitability}/100</span></td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
