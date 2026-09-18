import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { getNotifications } from '../api';

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

function BackendStatusBanner({ backendStatus }) {
  if (!backendStatus || backendStatus.status === 'ready') return null;

  const isStarting = backendStatus.status === 'checking';
  const title = isStarting ? 'WORKFORCE BACKEND CONNECTING' : 'WORKFORCE BACKEND UNAVAILABLE';
  const description = isStarting
    ? 'The workforce server is starting. Please wait a moment. Refresh the page once the connection is ready.'
    : 'The backend could not be reached. Please wait for the backend to connect, then refresh the page.';

  return (
    <div
      className={`backend-banner ${isStarting ? 'warning' : 'danger'}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="backend-banner__title">{title}</div>
      <div className="backend-banner__body">
        <span>{description}</span>
        <button type="button" className="backend-banner__button" onClick={backendStatus.retry}>
          {isStarting ? 'Check Again' : 'Try Again'}
        </button>
      </div>
    </div>
  );
}

export default function Layout({ backendStatus, children }) {
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const refreshNotifications = async () => {
      try {
        const res = await getNotifications(true);
        setUnreadCount(Array.isArray(res.data) ? res.data.length : 0);
      } catch (error) {
        setUnreadCount(0);
      }
    };
    refreshNotifications();
    const interval = setInterval(refreshNotifications, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      {backendStatus && <BackendStatusBanner backendStatus={backendStatus} />}
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
        {children || <Outlet />}
      </div>
    </div>
  );
}
