import axios from 'axios';

const API_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

export const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      error.message = 'The workforce API is unavailable.';
    }
    return Promise.reject(error);
  },
);

export const getDashboardStats = () => api.get('/dashboard/stats/');
export const getEmployees = () => api.get('/employees/');
export const getTasks = () => api.get('/tasks/');
export const getAssignments = () => api.get('/assignments/');
export const getEvents = () => api.get('/events/');

export const updateEmployee = (id, data) => api.patch(`/employees/${id}/`, data);

export const predictAllocation = (data) => api.post('/allocation/predict/', data);
export const assignTask = (data) => api.post('/allocation/assign/', data);
export const reallocateTask = (taskId) => api.post('/allocation/reallocate/', { task_id: taskId });
