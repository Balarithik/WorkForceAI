import { useState } from 'react';
import { queryCopilot } from '../api';

export default function Copilot() {
  const [question, setQuestion] = useState('Which employee should take the next high-priority task?');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleQuery = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await queryCopilot(question);
      setAnswer(res.data.answer || res.data.summary || 'No guidance returned.');
    } catch (error) {
      setAnswer('The copilot is unavailable right now.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>AI Manager Copilot</h2>
      <form onSubmit={handleQuery}>
        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={4} style={{ width: '100%', marginBottom: '12px' }} />
        <button type="submit" className="button" disabled={loading}>{loading ? 'Asking...' : 'Ask Copilot'}</button>
      </form>
      <div style={{ marginTop: '18px', padding: '12px', background: '#f8fafc', borderRadius: '12px' }}>
        <strong>Response</strong>
        <p style={{ marginTop: '8px', whiteSpace: 'pre-wrap' }}>{answer || 'No answer yet.'}</p>
      </div>
    </div>
  );
}
