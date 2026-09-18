import { useEffect, useState } from 'react';
import { getEvents } from '../api';

const FILTERS = ['ALL', 'ASSIGNMENTS', 'REALLOCATIONS', 'SLA', 'EMPLOYEE', 'TASKS', 'CRITICAL'];

const eventTypeLabels = {
  NEW_TASK: 'Task created',
  TASK_COMPLETED: 'Task completed',
  EMPLOYEE_UNAVAILABLE: 'Employee unavailable',
  REALLOCATION: 'Reallocation',
  SLA_RISK: 'SLA risk',
  ASSIGNMENT: 'Assignment',
  TASK_UPDATED: 'Task updated',
};

const severityMap = {
  LOW: 'info',
  MEDIUM: 'warning',
  HIGH: 'warning',
  CRITICAL: 'critical',
};

export default function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeFilter, setActiveFilter] = useState('ALL');

  useEffect(() => {
    getEvents()
      .then((res) => setEvents([...res.data].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))))
      .catch(() => setError('Unable to load events.'))
      .finally(() => setLoading(false));
  }, []);

  const filteredEvents = events.filter((event) => {
    if (activeFilter === 'ALL') return true;
    const type = String(event.event_type || '').toUpperCase();
    if (activeFilter === 'ASSIGNMENTS') return type.includes('ASSIGN') || type.includes('TASK');
    if (activeFilter === 'REALLOCATIONS') return type.includes('REALLOC');
    if (activeFilter === 'SLA') return type.includes('SLA');
    if (activeFilter === 'EMPLOYEE') return type.includes('EMPLOYEE');
    if (activeFilter === 'TASKS') return type.includes('TASK');
    if (activeFilter === 'CRITICAL') return (event.severity || 'MEDIUM').toUpperCase() === 'CRITICAL' || type.includes('CRITICAL');
    return true;
  });

  return (
    <div className="events-page">
      <div className="panel panel--tight">
        <div className="panel__header panel__header--stacked">
          <div>
            <p className="eyebrow">Activity</p>
            <h2>Recent events</h2>
          </div>
          <div className="event-filter-bar">
            {FILTERS.map((filter) => (
              <button
                key={filter}
                type="button"
                className={`filter-chip ${activeFilter === filter ? 'filter-chip--active' : ''}`}
                onClick={() => setActiveFilter(filter)}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        {error && <div className="result bad">Unable to load events.</div>}
        {loading && <div className="empty">Loading recent events...</div>}

        {!loading && !error && filteredEvents.length === 0 && <div className="empty">No workforce events yet.</div>}

        {!loading && !error && filteredEvents.length > 0 && (
          <div className="timeline">
            {filteredEvents.map((event) => {
              const createdAt = event.created_at ? new Date(event.created_at) : new Date();
              const eventType = event.event_type || 'TASK_UPDATE';
              const label = eventTypeLabels[eventType] || eventType.replaceAll('_', ' ');
              const severity = String(event.severity || 'MEDIUM').toUpperCase();
              const badgeClass = severityMap[severity] || 'info';

              return (
                <div className="timeline-item" key={event.id || `${eventType}-${createdAt.getTime()}`}>
                  <div className="timeline-time">{createdAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                  <div className="timeline-marker" aria-hidden="true" />
                  <div className="timeline-card">
                    <div className="timeline-head">
                      <span className="event-badge event-badge--type">{label}</span>
                      <span className={`event-badge event-badge--${badgeClass}`}>{severity}</span>
                    </div>
                    <h3>{event.title || label}</h3>
                    <p>{event.description || 'Workforce activity update.'}</p>
                    <div className="timeline-details">
                      {event.task && <span>Task: {event.task.task_id || event.task_id || event.task}</span>}
                      {event.employee && <span>Employee: {event.employee.name || event.employee}</span>}
                      <span>{createdAt.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
