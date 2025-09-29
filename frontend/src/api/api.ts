// src/api/api.ts
import axios, { AxiosHeaders, AxiosRequestHeaders } from "axios";

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

// helper seguro para setar Authorization em qualquer tipo de headers
function setAuthHeader(
  headers: AxiosRequestHeaders | AxiosHeaders | undefined,
  token: string,
) {
  if (!token) return headers;
  if (!headers) {
    return { Authorization: `Bearer ${token}` } as AxiosRequestHeaders;
  }
  const h: any = headers;
  if (typeof h.set === "function") {
    h.set("Authorization", `Bearer ${token}`); // AxiosHeaders
  } else {
    h.Authorization = `Bearer ${token}`; // plain object
  }
  return headers;
}

// Request: só mete Authorization se NÃO vier definido (para não pisar o refresh)
api.interceptors.request.use((config) => {
  const already = (config.headers as any)?.Authorization;
  const token = localStorage.getItem("access_token");
  if (token && !already) {
    config.headers = setAuthHeader(config.headers as any, token);
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original: any = error.config || {};
    const status = error?.response?.status;
    const url: string = original?.url || "";
    const isAuthPath = url.includes("/auth/login") || url.includes("/auth/refresh");

    if (status === 401 && !isAuthPath && !original._retry) {
      original._retry = true;

      if (isRefreshing) {
        const token = await new Promise<string | null>((resolve) => queue.push(resolve));
        if (token) original.headers = setAuthHeader(original.headers as any, token);
        return api(original);
      }

      isRefreshing = true;
      try {
        const refresh = localStorage.getItem("refresh_token");
        if (!refresh) throw new Error("no refresh token");

        const { data } = await api.post("/auth/refresh", null, {
          // enviamos o refresh token explicitamente no header
          headers: { Authorization: `Bearer ${refresh}` },
        });

        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) localStorage.setItem("refresh_token", data.refresh_token);

        queue.forEach((fn) => fn(data.access_token));
        queue = [];

        original.headers = setAuthHeader(original.headers as any, data.access_token);
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
  },
);

export default api;
