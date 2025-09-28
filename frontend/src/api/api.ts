
import axios from 'axios';
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api' });
let isRefreshing = false as boolean;
let queue: Array<(token: string | null) => void> = [];
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config || {};
    const status = error?.response?.status;
    const isAuthPath = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh');
    if (status === 401 && !isAuthPath && !original._retry) {
      original._retry = true;
      if (isRefreshing) {
        const token = await new Promise<string | null>((resolve) => queue.push(resolve));
        if (token) (original.headers ||= {}).Authorization = `Bearer ${token}`;
        return api(original);
      }
      isRefreshing = true;
      try {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) throw new Error('no refresh token');
        const { data } = await api.post('/auth/refresh', null, { headers: { Authorization: `Bearer ${refresh}` } });
        localStorage.setItem('access_token', data.access_token);
        queue.forEach((fn) => fn(data.access_token)); queue = [];
        (original.headers ||= {}).Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (e) {
        localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token');
        queue.forEach((fn) => fn(null)); queue = []; return Promise.reject(error);
      } finally { isRefreshing = false; }
    }
    return Promise.reject(error);
  }
);
export default api;
