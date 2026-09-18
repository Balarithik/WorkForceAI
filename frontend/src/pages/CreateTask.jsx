import { useState } from 'react';
import { predictAllocation, assignTask } from '../api';
import { CheckCircle2, ChevronRight, Loader2, AlertCircle } from 'lucide-react';

export default function CreateTask() {
  const [formData, setFormData] = useState({
    task_id: 'T' + Math.floor(Math.random() * 10000),
    title: '',
    description: '',
    task_type: 'Machine Learning',
    required_skills: '',
    priority: 'MEDIUM',
    estimated_effort_hours: 8,
    sla_hours: 24,
    remaining_sla_hours: 24,
    deadline: new Date(Date.now() + 86400000).toISOString().split('T')[0] + 'T18:00',
    location: 'Remote',
  });
  
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [assignedResult, setAssignedResult] = useState(null);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const payload = {
        ...formData,
        required_skills: formData.required_skills.split(',').map(s => s.trim()),
      };
      const res = await predictAllocation(payload);
      setCandidates(res.data.candidates);
    } catch (err) {
      const detail = err.response?.data?.detail || err.response?.data?.error || 'Failed to analyze candidates';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAssignment = async () => {
    setLoading(true);
    try {
      const payload = {
        ...formData,
        required_skills: formData.required_skills.split(',').map(s => s.trim()),
      };
      const res = await assignTask(payload);
      setAssignedResult(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.response?.data?.error || 'Failed to assign task';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  if (assignedResult) {
    return (
      <div className="bg-white p-8 rounded-lg shadow max-w-2xl mx-auto text-center border border-green-100">
        <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Assignment Successful</h2>
        <p className="text-gray-600 mb-6">Task "{formData.title}" has been successfully assigned.</p>
        
        <div className="bg-gray-50 rounded p-6 mb-6 text-left">
          <p className="text-sm text-gray-500 uppercase tracking-wider mb-1">Assigned To</p>
          <p className="text-lg font-medium text-gray-900 mb-4">{assignedResult.assigned_employee.name} ({assignedResult.assigned_employee.employee_id})</p>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Suitability Score</p>
              <p className="font-semibold text-indigo-600">{assignedResult.suitability_score.toFixed(1)}/100</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Predicted Completion</p>
              <p className="font-semibold text-gray-900">{assignedResult.predicted_completion_hours.toFixed(1)} hrs</p>
            </div>
          </div>
        </div>
        
        <button 
          onClick={() => { setAssignedResult(null); setCandidates([]); }}
          className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition"
        >
          Create Another Task
        </button>
      </div>
    );
  }

  return (
    <div className="flex gap-6 max-w-7xl mx-auto">
      {/* Form Section */}
      <div className="flex-1 bg-white p-6 rounded-lg shadow border border-gray-100">
        <h3 className="text-lg font-medium text-gray-800 mb-6">Create New Task</h3>
        <form onSubmit={handleAnalyze} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700">Task Title</label>
              <input type="text" name="title" required value={formData.title} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea name="description" rows="3" value={formData.description} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Task Type</label>
              <input type="text" name="task_type" value={formData.task_type} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Required Skills (comma separated)</label>
              <input type="text" name="required_skills" value={formData.required_skills} onChange={handleChange} placeholder="Python, Machine Learning" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Priority</label>
              <select name="priority" value={formData.priority} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2 bg-white">
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Location</label>
              <input type="text" name="location" value={formData.location} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Estimated Effort (Hours)</label>
              <input type="number" step="0.1" name="estimated_effort_hours" value={formData.estimated_effort_hours} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">SLA Hours</label>
              <input type="number" step="0.1" name="sla_hours" value={formData.sla_hours} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 border p-2" />
            </div>
          </div>

          <div className="pt-4 border-t border-gray-100">
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {loading && candidates.length === 0 ? <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" /> : null}
              Analyze Candidates & Recommend Assignment
            </button>
          </div>
        </form>
        
        {error && (
          <div className="mt-4 bg-red-50 p-4 border border-red-200 rounded-md flex items-center text-red-700">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}
      </div>

      {/* Results Section */}
      <div className="flex-1">
        {candidates.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow border border-gray-100 space-y-6">
            <h3 className="text-lg font-medium text-gray-800">AI Assignment Recommendation</h3>
            
            {/* Top Candidate */}
            <div className="bg-indigo-50 rounded-lg p-5 border border-indigo-100">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-sm text-indigo-600 font-semibold tracking-wide uppercase">Recommended Employee</p>
                  <h4 className="text-xl font-bold text-gray-900 mt-1">{candidates[0].name}</h4>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Suitability Score</p>
                  <p className="text-2xl font-bold text-indigo-700">{candidates[0].suitability_score.toFixed(1)}<span className="text-sm text-indigo-400">/100</span></p>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 border-t border-indigo-100 pt-4">
                <div>
                  <p className="text-xs text-gray-500">Success Prob.</p>
                  <p className="font-semibold text-gray-900">{(candidates[0].success_probability * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">SLA Prob.</p>
                  <p className="font-semibold text-gray-900">{(candidates[0].sla_probability * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Predicted Time</p>
                  <p className="font-semibold text-gray-900">{candidates[0].predicted_completion_hours.toFixed(1)} h</p>
                </div>
              </div>
              
              <button 
                onClick={handleConfirmAssignment}
                disabled={loading}
                className="mt-5 w-full bg-indigo-600 text-white py-2 rounded-md hover:bg-indigo-700 font-medium transition flex justify-center items-center"
              >
                {loading ? <Loader2 className="animate-spin mr-2 w-5 h-5" /> : <CheckCircle2 className="mr-2 w-5 h-5" />}
                Confirm Assignment
              </button>
            </div>
            
            {/* Other Candidates */}
            <div>
              <h4 className="font-medium text-gray-700 mb-3 flex items-center">
                Other Candidates <ChevronRight className="w-4 h-4 ml-1 text-gray-400" />
              </h4>
              <div className="overflow-hidden border border-gray-200 sm:rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Match</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {candidates.slice(1, 4).map((c, i) => (
                      <tr key={i}>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{c.name}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{(c.skill_match_score * 100).toFixed(0)}%</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-indigo-600">{c.suitability_score.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
          </div>
        )}
      </div>
    </div>
  );
}
