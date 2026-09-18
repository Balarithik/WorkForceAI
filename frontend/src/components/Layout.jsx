import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { getNotifications } from '../api';
import useBackendHealth from '../hooks/useBackendHealth';

const navItems = [
  { label: 'Create Task', to: '/create-task' },
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Employees', to: '/employees' },
  { label: 'Tasks', to: '/tasks' },
  { label: 'Assignments', to: '/assignments' },
  { label: 'Events', to: '/events' },
  { label: 'SLA Risk', to: '/sla-risk' },
  { label: 'Decision History', to: '/decision-history' },
];

function BackendStatusBanner({ status, error, retry }) {
  const isUnavailable = status === 'unavailable';

  if (status === 'ready') {
    return null;
  }

  return (
    <div className={`backend-banner ${isUnavailable ? 'backend-banner--unavailable' : 'backend-banner--checking'}`} role="status" aria-live="polite">
      <div className="backend-banner__content">
        <strong>{isUnavailable ? 'WORKFORCE BACKEND UNAVAILABLE' : 'WORKFORCE BACKEND CONNECTING'}</strong>
        <span>
          {isUnavailable
            ? 'The workforce backend could not be reached. Please wait a moment and try again.'
            : 'The workforce server is starting. Please wait a moment and refresh the page once the connection is ready.'}
        </span>
        {error && <small>{error}</small>}
      </div>
      <button type="button" className="backend-banner__button" onClick={retry}>
        Check Again
      </button>
    </div>
  );
}

export default function Layout() {
  const [unreadCount, setUnreadCount] = useState(0);
  const { status, error, retry } = useBackendHealth();

  useEffect(() => {
    if (status !== 'ready') {
      return undefined;
    }

    const refreshNotifications = async () => {
      try {
        const res = await getNotifications(true);
        setUnreadCount(Array.isArray(res.data) ? res.data.length : 0);
      } catch {
        setUnreadCount(0);
      }
    };
    refreshNotifications();
    const interval = setInterval(refreshNotifications, 15000);
    return () => clearInterval(interval);
  }, [status]);

  return (
    <div>
      <div className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <div className="mark">AI</div>
            <div>
              <h1>WorkForceAI</h1>
              <span>Workforce assignment</span>
            </div>
          </div>
          <div className="stats">
            <div className="stat">
              <b>{unreadCount}</b>
              <span>Notifications</span>
            </div>
          </div>
        </div>
      </div>
      <div className="wrap wrap--status">
        <BackendStatusBanner status={status} error={error} retry={retry} />
      </div>
      <div className="wrap">
        <nav style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '18px' }}>
          {navItems.map(({ label, to }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({
                border: '1px solid #e2e4e9',
                borderRadius: '999px',
                padding: '8px 12px',
                textDecoration: 'none',
                fontWeight: 600,
                color: isActive ? '#0a4fd6' : '#374151',
                background: isActive ? '#eaf0fd' : '#fff',
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>
        {status === 'ready' ? <Outlet /> : <div className="card empty">{status === 'checking' ? 'Waiting for backend...' : 'Unable to connect to the workforce backend.'}</div>}
      </div>
    </div>
  );
}
