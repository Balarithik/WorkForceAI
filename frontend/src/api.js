import axios from 'axios';

const API_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

export const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      error.message = 'Cannot reach workforce backend. Check network and CORS configuration.';
    } else if (error.response.status === 403) {
      error.message = 'Backend rejected the request (403). Check CORS and CSRF configuration.';
    } else if (error.response.status === 404) {
      error.message = 'API endpoint not found (404). Check the API URL path.';
    } else if (error.response.status >= 500) {
      error.message = `Backend returned an internal server error (${error.response.status}).`;
    }
    return Promise.reject(error);
  },
);

export const getDashboardStats = () => api.get('/dashboard/stats/');
export const getHealthStatus = () => api.get('/health/');
export const getEmployees = () => api.get('/employees/');
export const getTasks = () => api.get('/tasks/');
export const getAssignments = () => api.get('/assignments/');
export const getEvents = () => api.get('/events/');
export const getSlaRisks = () => api.get('/sla-risks/');
export const getNotifications = (unreadOnly = false) => api.get(`/notifications/?unread_only=${String(unreadOnly).toLowerCase()}`);
export const markNotificationRead = (id) => api.patch(`/notifications/${id}/read/`);
export const markAllNotificationsRead = () => api.post('/notifications/read-all/');
export const getDecisions = () => api.get('/decisions/');
export const getTaskDecisionHistory = (taskId) => api.get(`/tasks/${taskId}/decision-history/`);

export const updateEmployee = (id, data) => api.patch(`/employees/${id}/`, data);

export const predictAllocation = (data) => api.post('/allocation/predict/', data);
export const assignTask = (data) => api.post('/allocation/assign/', data);
export const reallocateTask = (taskId) => api.post('/allocation/reallocate/', { task_id: taskId });
