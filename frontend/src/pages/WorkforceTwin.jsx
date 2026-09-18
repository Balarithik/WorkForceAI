import { useEffect, useState } from 'react';
import { getWorkforceTwin } from '../api';

export default function WorkforceTwin() {
  const [twin, setTwin] = useState(null);

  useEffect(() => {
    getWorkforceTwin().then((res) => setTwin(res.data)).catch(() => setTwin(null));
  }, []);

  if (!twin) return <div className="card empty">Loading workforce digital twin...</div>;

  return (
    <div className="card">
      <h2>Workforce Digital Twin</h2>
      <div className="grid two">
        <div className="mini-card">
          <h3>Capacity</h3>
          <p>{twin.capacity ?? 'N/A'}</p>
        </div>
        <div className="mini-card">
          <h3>Utilization</h3>
          <p>{twin.utilization ?? 'N/A'}</p>
        </div>
        <div className="mini-card">
          <h3>Risk</h3>
          <p>{twin.risk ?? 'N/A'}</p>
        </div>
        <div className="mini-card">
          <h3>Recommended Action</h3>
          <p>{twin.recommendation ?? 'N/A'}</p>
        </div>
      </div>
      <div style={{ marginTop: '16px' }}>
        <h3>Team Snapshot</h3>
        <pre style={{ background: '#f8fafc', padding: '12px', borderRadius: '10px', overflowX: 'auto' }}>
          {JSON.stringify(twin.snapshot || twin, null, 2)}
        </pre>
      </div>
    </div>
  );
}
