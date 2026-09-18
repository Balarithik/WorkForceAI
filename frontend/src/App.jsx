import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import useBackendHealth from './hooks/useBackendHealth';
import Dashboard from './pages/Dashboard';
import CreateTask from './pages/CreateTask';
import Employees from './pages/Employees';
import Tasks from './pages/Tasks';
import Assignments from './pages/Assignments';
import Events from './pages/Events';
import SlaRisk from './pages/SlaRisk';
import DecisionHistory from './pages/DecisionHistory';

function WaitingForBackend({ backendStatus }) {
  return (
    <div className="wrap">
      <div className="card empty">
        {backendStatus.status === 'unavailable' ? 'Unable to connect to the workforce backend.' : 'Waiting for backend...'}
      </div>
    </div>
  );
}

function App() {
  const backendStatus = useBackendHealth();

  if (backendStatus.status !== 'ready') {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="*" element={<Layout backendStatus={backendStatus}><WaitingForBackend backendStatus={backendStatus} /></Layout>} />
        </Routes>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout backendStatus={backendStatus} />}>
          <Route index element={<CreateTask />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="create-task" element={<CreateTask />} />
          <Route path="employees" element={<Employees />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="assignments" element={<Assignments />} />
          <Route path="events" element={<Events />} />
          <Route path="sla-risk" element={<SlaRisk />} />
          <Route path="decision-history" element={<DecisionHistory />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
