// src/api/api.ts
import axios from "axios";

const base =
  (import.meta.env as any).VITE_API_BASE ||
  (import.meta.env as any).VITE_API_BASE_URL ||
  "http://localhost:5000/api";

const api = axios.create({
  baseURL: base.replace(/\/+$/, ""),
  withCredentials: false,
});

let isRefreshing = false as boolean;
let queue: Array<(token: string | null) => void> = [];

// Só define Authorization se ainda não existir (para não pisar o refresh header)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && !config.headers?.Authorization) {
    (config.headers ||= {}).Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config || {};
    const status = error?.response?.status;
    const url: string = original?.url || "";
    const isAuthPath = url.includes("/auth/login") || url.includes("/auth/refresh");

    if (status === 401 && !isAuthPath && !original._retry) {
      original._retry = true;

      if (isRefreshing) {
        const token = await new Promise<string | null>((resolve) => queue.push(resolve));
        if (token) (original.headers ||= {}).Authorization = `Bearer ${token}`;
        return api(original);
      }

      isRefreshing = true;
      try {
        const refresh = localStorage.getItem("refresh_token");
        if (!refresh) throw new Error("no refresh token");

        // NOTE: passamos o refresh token no header; como o request interceptor
        // já não pisa Authorization, isto funciona.
        const { data } = await api.post("/auth/refresh", null, {
          headers: { Authorization: `Bearer ${refresh}` },
        });

        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }

        queue.forEach((fn) => fn(data.access_token));
        queue = [];

        (original.headers ||= {}).Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (e) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        queue.forEach((fn) => fn(null));
        queue = [];
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
