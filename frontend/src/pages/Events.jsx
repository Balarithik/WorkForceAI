import { useEffect, useMemo, useState } from 'react';
import { getEvents } from '../api';
import { Activity, AlertTriangle, BellRing, BriefcaseBusiness, CircleDashed, UserRoundCog, Users } from 'lucide-react';

const FILTERS = ['All', 'Assignments', 'Reallocations', 'SLA', 'Employee', 'Tasks', 'Critical'];

const severityMap = (eventType = '') => {
  const type = eventType.toUpperCase();
  if (type.includes('CRITICAL') || type.includes('HIGH')) return 'CRITICAL';
  if (type.includes('SLA') || type.includes('REALLOCATION') || type.includes('DELAYED')) return 'HIGH';
  if (type.includes('UNAVAILABLE') || type.includes('WORKLOAD') || type.includes('CHANGED')) return 'WARNING';
  return 'INFO';
};

const typeLabel = (eventType = '') => eventType.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

const typeIcon = (eventType = '') => {
  const type = eventType.toUpperCase();
  if (type.includes('UNAVAILABLE') || type.includes('AVAILABLE')) return UserRoundCog;
  if (type.includes('REALLOC')) return BriefcaseBusiness;
  if (type.includes('SLA')) return AlertTriangle;
  if (type.includes('TASK')) return BellRing;
  if (type.includes('CRITICAL')) return CircleDashed;
  return Activity;
};

export default function Events() {
  const [events, setEvents] = useState([]);
  const [filter, setFilter] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getEvents()
      .then((res) => {
        const sorted = [...(res.data || [])].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        setEvents(sorted);
      })
      .catch(() => setError('Unable to load events.'))
      .finally(() => setLoading(false));
  }, []);

  const filteredEvents = useMemo(() => {
    if (filter === 'All') return events;
    const normalized = filter.toUpperCase();
    return events.filter((event) => {
      const type = (event.event_type || '').toUpperCase();
      if (normalized === 'ASSIGNMENTS' && (type.includes('TASK') || type.includes('ASSIGN'))) return true;
      if (normalized === 'REALLOCATIONS' && type.includes('REALLOC')) return true;
      if (normalized === 'SLA' && type.includes('SLA')) return true;
      if (normalized === 'EMPLOYEE' && (type.includes('EMPLOYEE') || type.includes('UNAVAILABLE') || type.includes('AVAILABLE'))) return true;
      if (normalized === 'TASKS' && type.includes('TASK')) return true;
      if (normalized === 'CRITICAL' && (type.includes('CRITICAL') || severityMap(event.event_type) === 'CRITICAL')) return true;
      return false;
    });
  }, [events, filter]);

  return (
    <div className="event-page">
      <header className="card event-header">
        <div>
          <p className="eyebrow">Activity feed</p>
          <h2>Recent Events</h2>
        </div>
        <div className="event-filters" aria-label="Event filters">
          {FILTERS.map((item) => (
            <button
              key={item}
              type="button"
              className={`filter-button ${filter === item ? 'active' : ''}`}
              onClick={() => setFilter(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </header>

      {error && <div className="card result bad">{error}</div>}
      {loading && <div className="card empty">Loading recent events...</div>}

      {!loading && !error && (
        <div className="timeline card">
          {filteredEvents.length === 0 ? (
            <div className="empty-state">No workforce events yet.</div>
          ) : (
            filteredEvents.map((event) => {
              const Icon = typeIcon(event.event_type);
              const severity = severityMap(event.event_type);
              const timestamp = new Date(event.created_at);
              return (
                <article key={event.id} className="event-item">
                  <div className="event-time">
                    <span>{timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <div className={`event-dot ${severity.toLowerCase()}`}>
                    <Icon size={14} />
                  </div>
                  <div className="event-body">
                    <div className="event-title-row">
                      <div className="event-type">{typeLabel(event.event_type)}</div>
                      <span className={`severity-badge ${severity.toLowerCase()}`}>{severity}</span>
                    </div>
                    <h3>{event.description}</h3>
                    <div className="event-meta">
                      {event.task_details?.task_id && <span>Task: {event.task_details.task_id}</span>}
                      {event.employee_details?.name && <span>Employee: {event.employee_details.name}</span>}
                      <span>{timestamp.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>
                    </div>
                  </div>
                </article>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
