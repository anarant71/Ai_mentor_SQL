import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status !== 401 || error.config?.url === '/auth/refresh') {
      return Promise.reject(error);
    }

    // /auth/me is expected to 401 for unauthenticated users — skip redirect
    if (error.config?.url === '/auth/me') {
      return Promise.reject(error);
    }

    // Avoid redirect loop if we're already on /login
    if (window.location.pathname === '/login') {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return Promise.reject(error);
    }

    isRefreshing = true;
    try {
      await api.post('/auth/refresh');
      return api(error.config);
    } catch {
      window.location.href = '/login';
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  },
);

export default api;