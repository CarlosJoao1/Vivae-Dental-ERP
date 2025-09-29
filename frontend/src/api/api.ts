// src/api/api.ts
import axios, { AxiosHeaders } from "axios";

/**
 * Base URL da API:
 * - Usa VITE_API_BASE ou VITE_API_BASE_URL (Render/produção)
 * - Fallback para http://localhost:5000/api (dev local)
 */
const env = import.meta.env as any;
const base =
  (env?.VITE_API_BASE as string) ||
  (env?.VITE_API_BASE_URL as string) ||
  "http://localhost:5000/api";

const api = axios.create({
  baseURL: base.replace(/\/+$/, ""), // remove / no fim
  withCredentials: false,
});

// Estado de refresh em curso + fila de callbacks
let isRefreshing = false;
let queue: Array<(token: string | null) => void> = [];

/**
 * Normaliza SEMPRE os headers para AxiosHeaders e define Authorization,
 * sem sobrepor se já existir.
 */
function ensureAuthHeader(headers: unknown, token?: string | null): AxiosHeaders {
  const h = AxiosHeaders.from(headers ?? {}); // nunca undefined
  if (token && !h.has("Authorization")) {
    h.set("Authorization", `Bearer ${token}`);
  }
  return h;
}

/** Interceptor de request:
 *  - injeta Bearer access_token se não houver Authorization já definido
 */
api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  config.headers = ensureAuthHeader(config.headers, token);
  return config;
});

/** Interceptor de response:
 *  - Em 401 (fora de /auth/login e /auth/refresh), tenta refresh com fila
 */
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original: any = error.config || {};
    const status: number | undefined = error?.response?.status;
    const url: string = original?.url || "";
    const isAuthPath = url.includes("/auth/login") || url.includes("/auth/refresh");

    if (status === 401 && !isAuthPath && !original._retry) {
      original._retry = true;

      // Se já há um refresh a decorrer, aguarda na fila
      if (isRefreshing) {
        const token = await new Promise<string | null>((resolve) => queue.push(resolve));
        original.headers = ensureAuthHeader(original.headers, token ?? undefined);
        return api(original);
      }

      // Começa refresh
      isRefreshing = true;
      try {
        const refresh = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
        if (!refresh) throw new Error("no refresh token");

        // Faz refresh passando o refresh_token no Authorization (não é pisado pelo request interceptor)
        const { data } = await api.post("/auth/refresh", null, {
          headers: { Authorization: `Bearer ${refresh}` },
        });

        // Guarda novos tokens (se vier novo refresh_token, atualiza)
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", data.access_token);
          if (data.refresh_token) localStorage.setItem("refresh_token", data.refresh_token);
        }

        // Liberta a fila com o novo access_token
        queue.forEach((fn) => fn(data.access_token));
        queue = [];

        // Reenvia a request original com o novo access_token
        original.headers = ensureAuthHeader(original.headers, data.access_token);
        return api(original);
      } catch (e) {
        // Falhou refresh: limpa tokens e falha todas as pendentes
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
        queue.forEach((fn) => fn(null));
        queue = [];
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    // Outro erro qualquer
    return Promise.reject(error);
  }
);

export default api;
