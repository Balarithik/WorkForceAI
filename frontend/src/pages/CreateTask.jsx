import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { assignTask, getAssignments, getEmployees, getEvents, getTasks, predictAllocation, updateEmployee } from '../api';

const SKILLS = ['Java', 'Python', 'React', 'Database', 'Kubernetes', 'Security', 'Testing'];
const PRIORITIES = [
  { label: 'Critical', value: 'CRITICAL', css: 'p0' },
  { label: 'High', value: 'HIGH', css: 'p1' },
  { label: 'Normal', value: 'MEDIUM', css: 'p2' },
  { label: 'Low', value: 'LOW', css: 'p3' },
];

const initials = (name = '') => name.split(' ').map((word) => word[0]).join('').slice(0, 2);
const DEFAULT_DEADLINE = new Date(Date.now() + 86400000).toISOString();
const errorMessage = (error, fallback) => {
  const responseData = error.response?.data;
  if (responseData?.detail || responseData?.error) return responseData.detail || responseData.error;
  if (responseData && typeof responseData === 'object') {
    return Object.entries(responseData).map(([field, messages]) => `${field}: ${[].concat(messages).join(', ')}`).join(' ');
  }
  return error.message || fallback;
};

function ScoreBreakdown({ candidate }) {
  const breakdown = candidate.score_breakdown || {};
  return (
    <div className="score-breakdown">
      <div><span>Skill match</span><b>{Math.round((candidate.skill_match_score || 0) * 100)}%</b></div>
      <div><span>Current workload</span><b>{candidate.current_workload_percent}%</b></div>
      <div><span>Available capacity</span><b>{candidate.available_capacity_percent ?? Math.max(100 - candidate.current_workload_percent, 0)}%</b></div>
      <div><span>Success probability</span><b>{((candidate.success_probability || 0) * 100).toFixed(1)}%</b></div>
      <div><span>SLA probability</span><b>{((candidate.sla_probability || 0) * 100).toFixed(1)}%</b></div>
      <div><span>Predicted completion</span><b>{Number(candidate.predicted_completion_hours || 0).toFixed(1)}h</b></div>
      <div><span>Time score</span><b>{((candidate.time_score || 0) * 100).toFixed(1)}%</b></div>
      <div><span>Score contribution</span><b>{Number(breakdown.success_contribution || 0).toFixed(1)} + {Number(breakdown.sla_contribution || 0).toFixed(1)} + {Number(breakdown.time_contribution || 0).toFixed(1)}</b></div>
    </div>
  );
}

export default function CreateTask() {
  const [formData, setFormData] = useState({
    task_id: '',
    title: '',
    description: '',
    task_type: 'Software Development',
    priority: 'MEDIUM',
    required_skills: [],
    estimated_effort_hours: 3,
    sla_hours: 24,
    remaining_sla_hours: 24,
    deadline: DEFAULT_DEADLINE,
    location: 'Remote',
  });
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [events, setEvents] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [assignedResult, setAssignedResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true);
    const results = await Promise.allSettled([getEmployees(), getTasks(), getAssignments(), getEvents()]);
    const [employeeResult, taskResult, assignmentResult, eventResult] = results;
    if (employeeResult.status === 'fulfilled') setEmployees(employeeResult.value.data);
    if (taskResult.status === 'fulfilled') setTasks(taskResult.value.data);
    if (assignmentResult.status === 'fulfilled') setAssignments(assignmentResult.value.data);
    if (eventResult.status === 'fulfilled') setEvents(eventResult.value.data);

    const failedResult = results.find((result) => result.status === 'rejected');
    setError(failedResult ? errorMessage(failedResult.reason, 'Unable to load workforce data.') : '');
    setLoading(false);
  };

  useEffect(() => { refresh(); }, []);

  const updateField = (name, value) => setFormData((current) => ({ ...current, [name]: value }));
  const availableCount = employees.filter((employee) => employee.availability === 'AVAILABLE').length;
  const activeAssignments = assignments.filter((assignment) => assignment.status === 'ACTIVE');
  const waitingCount = tasks.filter((task) => task.status === 'PENDING').length;
  const recommendedEmployeeId = candidates[0]?.employee_id;
  const rankedEmployees = useMemo(() => {
    const requiredSkills = new Set(formData.required_skills.map((skill) => skill.toLowerCase()));
    const feasibility = (employee) => {
      const skills = (employee.skills || []).map((skill) => skill.toLowerCase());
      const matchedSkills = skills.filter((skill) => requiredSkills.has(skill)).length;
      return {
        available: employee.availability === 'AVAILABLE' ? 1 : 0,
        matchedSkills,
        performance: Number(employee.historical_performance_score) || 0,
        capacity: 100 - (Number(employee.current_workload_percent) || 0),
      };
    };
    return [...employees].sort((left, right) => {
      const a = feasibility(left);
      const b = feasibility(right);
      return (right.employee_id === recommendedEmployeeId ? 1 : 0) - (left.employee_id === recommendedEmployeeId ? 1 : 0) || b.available - a.available || b.matchedSkills - a.matchedSkills || b.performance - a.performance || b.capacity - a.capacity;
    });
  }, [employees, formData.required_skills, recommendedEmployeeId]);

  const toggleSkill = (skill) => {
    const skills = formData.required_skills.includes(skill)
      ? formData.required_skills.filter((value) => value !== skill)
      : [...formData.required_skills, skill];
    updateField('required_skills', skills);
  };

  const toggleAvailability = async (employee) => {
    setError('');
    try {
      await updateEmployee(employee.id, {
        availability: employee.availability === 'AVAILABLE' ? 'UNAVAILABLE' : 'AVAILABLE',
      });
      await refresh();
    } catch (requestError) {
      setError(errorMessage(requestError, 'Unable to update employee availability.'));
    }
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!formData.title.trim() || !formData.required_skills.length) {
      setError('Provide a task name and at least one required skill.');
      return;
    }
    setSubmitting(true);
    setError('');
    setAssignedResult(null);
    try {
      const payload = { ...formData, task_id: formData.task_id || `T${Date.now()}` };
      setFormData(payload);
      const response = await predictAllocation(payload);
      setCandidates(response.data.candidates || []);
    } catch (requestError) {
      setError(errorMessage(requestError, 'Unable to analyze the available workforce.'));
    } finally {
      setSubmitting(false);
    }
  };

  const confirmAssignment = async () => {
    setSubmitting(true);
    setError('');
    try {
      const response = await assignTask({ ...formData, task_id: formData.task_id || `T${Date.now()}`, employee_id: candidates[0]?.employee_id });
      setAssignedResult(response.data);
      setCandidates([]);
      await refresh();
    } catch (requestError) {
      setError(errorMessage(requestError, 'Unable to assign task.'));
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setFormData((current) => ({ ...current, task_id: `T${Date.now()}`, title: '', description: '', required_skills: [] }));
    setCandidates([]);
    setAssignedResult(null);
    setError('');
  };

  return (
    <div>
      <div className="wrap">
        <section className="card">
          <h2>Assign Task</h2>
          <form onSubmit={submit} className="form">
            <div className="f"><label htmlFor="title">Task Name</label><input id="title" value={formData.title} onChange={(event) => updateField('title', event.target.value)} placeholder="Task name" /></div>
            <div className="f"><label htmlFor="priority">Priority</label><select id="priority" value={formData.priority} onChange={(event) => updateField('priority', event.target.value)}>{PRIORITIES.map((priority) => <option key={priority.value} value={priority.value}>{priority.label}</option>)}</select></div>
            <div className="f"><label htmlFor="hours">Work Hours</label><input id="hours" type="number" min="0.1" step="0.1" value={formData.estimated_effort_hours} onChange={(event) => updateField('estimated_effort_hours', Number(event.target.value))} /></div>
            <div className="f"><label htmlFor="sla">Due In (hours)</label><input id="sla" type="number" min="0.1" step="0.1" value={formData.sla_hours} onChange={(event) => setFormData((current) => ({ ...current, sla_hours: Number(event.target.value), remaining_sla_hours: Number(event.target.value) }))} /></div>
            <div className="skillrow"><label>Skills Required (select one or more)</label><div className="skillpick">{SKILLS.map((skill) => <button key={skill} type="button" className={`chip ${formData.required_skills.includes(skill) ? 'active' : ''}`} onClick={() => toggleSkill(skill)} aria-pressed={formData.required_skills.includes(skill)}>{skill}</button>)}</div></div>
            <div className="assign"><button className="btn primary" type="submit" disabled={submitting || loading || !formData.title.trim() || !formData.required_skills.length}>{submitting ? <Loader2 size={16} className="spin" /> : null} Assign Task</button><button className="btn quiet" type="button" onClick={reset}>Reset</button></div>
          </form>
          {error && <div className="result bad" role="alert"><AlertCircle size={16} /> {error}</div>}
          {assignedResult && <div className="result"><CheckCircle2 size={16} /> <b>{assignedResult.task_id}</b> assigned to <b>{assignedResult.assigned_employee?.name}</b>. {assignedResult.workload && <span>Workload updated: {assignedResult.workload.previous}% &rarr; {assignedResult.workload.new}%. Available capacity: {assignedResult.workload.capacity}%.</span>}</div>}
          {!error && candidates.length > 0 && <div className="result"><b>{candidates[0].employee?.name || candidates[0].name}</b> ({candidates[0].employee_id}) is the recommended match. Fit <b>{Number(candidates[0].suitability_score || 0).toFixed(1)}/100</b>. <span className="sub">Prediction generated by ML models.</span><ScoreBreakdown candidate={candidates[0]} /><button className="btn primary small" type="button" onClick={confirmAssignment} disabled={submitting}>Confirm Assignment</button></div>}
          {!error && candidates.length > 1 && <div className="candidate-list"><h3>Candidate comparison</h3><table><thead><tr><th>Employee</th><th>Skill match</th><th>Workload</th><th>Capacity</th><th>Success</th><th>SLA</th><th>Completion</th><th>Fit</th></tr></thead><tbody>{candidates.slice(0, 10).map((candidate) => <tr key={candidate.employee_id}><td><b>{candidate.employee?.name || candidate.name}</b><div className="tmeta">{candidate.employee_id}</div></td><td>{Math.round((candidate.skill_match_score || 0) * 100)}%</td><td>{candidate.current_workload_percent}%</td><td>{candidate.available_capacity_percent}%</td><td>{((candidate.success_probability || 0) * 100).toFixed(1)}%</td><td>{((candidate.sla_probability || 0) * 100).toFixed(1)}%</td><td>{Number(candidate.predicted_completion_hours || 0).toFixed(1)}h</td><td><b>{Number(candidate.suitability_score || 0).toFixed(1)}</b></td></tr>)}</tbody></table></div>}
        </section>

        {loading ? <div className="card empty">Loading workforce data...</div> : <div className="cols">
          <section className="card"><h2>Team · most feasible first</h2>{rankedEmployees.length === 0 ? <div className="empty">No employees found.</div> : rankedEmployees.map((employee) => <div className={`member ${employee.availability !== 'AVAILABLE' ? 'out' : ''}`} key={employee.id}><div className="avatar">{initials(employee.name)}</div><div style={{ flex: 1 }}><div className="top"><div><div className="name">{employee.name}</div><div className="sub">{employee.department} · {employee.location}</div></div><span className={`pill ${employee.availability === 'AVAILABLE' ? 'on' : 'off'}`}>{employee.availability}</span></div><div className="tags">{(employee.skills || []).map((skill) => <span className={`tag ${formData.required_skills.includes(skill) ? 'match' : ''}`} key={skill}>{skill}</span>)}<span className="tag">rating {employee.historical_performance_score}</span></div><div className="barline"><div className="bar"><i style={{ width: `${employee.availability === 'AVAILABLE' ? employee.current_workload_percent : 100 - 100}%` }} /></div><span>Workload {employee.current_workload_percent}% · Capacity {employee.availability === 'AVAILABLE' ? Math.max(100 - employee.current_workload_percent, 0) : 0}%</span></div><button className="btn small" type="button" onClick={() => toggleAvailability(employee)}>{employee.availability === 'AVAILABLE' ? 'Mark unavailable' : 'Mark available'}</button></div></div>)}</section>
          <div><section className="card"><h2>Assignments</h2>{tasks.length === 0 ? <div className="empty">No active tasks.</div> : <table><thead><tr><th>Task</th><th>Priority</th><th>Status</th><th>Owner</th></tr></thead><tbody>{tasks.map((task) => { const assignment = activeAssignments.find((item) => item.task === task.id); const owner = assignment?.employee_details; const priority = PRIORITIES.find((item) => item.value === task.priority) || PRIORITIES[2]; return <tr key={task.id}><td><div className="tname">{task.title}</div><div className="tmeta">{task.task_id} · {task.estimated_effort_hours}h</div></td><td><span className={`prio ${priority.css}`}>{priority.label}</span></td><td>{task.status}</td><td>{owner ? <div className="owner"><div className="avatar">{initials(owner.name)}</div>{owner.name}</div> : <span className="none">None</span>}</td></tr>; })}</tbody></table>}</section><section className="card log"><h2>Change Log</h2>{events.length === 0 ? <div className="empty">No events found.</div> : events.slice(0, 10).map((event) => <div className="change" key={event.id}><time>{new Date(event.created_at).toLocaleTimeString()}</time><div><b>{event.event_type.replaceAll('_', ' ')}</b><br />{event.description}</div></div>)}</section></div>
        </div>}
      </div>
    </div>
  );
}
