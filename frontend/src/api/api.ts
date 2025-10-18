// src/api/api.ts
import axios, { AxiosHeaders } from "axios";

/**
 * Base URL da API:
 * - Preferir VITE_API_BASE ou VITE_API_BASE_URL (mesmo em dev)
 * - Se não existir, em dev usa "/api" (Vite proxy)
 * - Fallback: http://localhost:5000/api
 */
const env = import.meta.env as any;

const isDev = env?.DEV === true;
const rawEnvBase = (env?.VITE_API_BASE as string) || (env?.VITE_API_BASE_URL as string) || "";

function withApiSuffix(u: string): string {
  const clean = (u || "").replace(/\/+$/, "");
  return clean.endsWith("/api") ? clean : `${clean}/api`;
}

// Determine base
// - DEV: prefer env; if missing, fallback to localhost:5000/api
// - PROD: require env; if missing, use relative '/api' (never localhost)
const base = rawEnvBase
  ? withApiSuffix(rawEnvBase)
  : (isDev ? "http://localhost:5000/api" : "/api");

const api = axios.create({
  baseURL: base.replace(/\/+$/, ""),
  withCredentials: false,
  // Render pode demorar no cold start; em produção, dá mais margem
  timeout: isDev ? 20000 : 60000,
});

console.log('[API] Environment:', isDev ? 'development' : 'production');
console.log('[API] Base URL configured:', base.replace(/\/+$/, ""));

// Estado de refresh + fila de callbacks
let isRefreshing = false;
let queue: Array<(token: string | null) => void> = [];

/**
 * Garante um AxiosHeaders (nunca undefined) e define Authorization
 * apenas se ainda não existir.
 */
function ensureAuthHeader(headers: unknown, token?: string | null): AxiosHeaders {
  const h =
    headers instanceof AxiosHeaders
      ? headers
      : headers
      ? AxiosHeaders.from(headers as any)
      : new AxiosHeaders(); // <- evita passar {}

  if (token && !h.has("Authorization")) {
    h.set("Authorization", `Bearer ${token}`);
    }
  return h;
}

/** Interceptor de request:
 *  - injeta Bearer access_token se não houver Authorization já definido
 */
api.interceptors.request.use(
  (config) => {
    const token = typeof globalThis.window !== "undefined" ? localStorage.getItem("access_token") : null;
    config.headers = ensureAuthHeader(config.headers, token);
    // Propagate selected tenant to backend if present
    try {
      const tid = typeof globalThis.window !== 'undefined' ? localStorage.getItem('tenant_id') : null;
      if (tid) {
        const h = config.headers instanceof AxiosHeaders ? config.headers : AxiosHeaders.from(config.headers as any);
        if (!h.has('X-Tenant-Id')) h.set('X-Tenant-Id', tid);
        config.headers = h;
      }
      // Propagate language preference to backend
      const lang = typeof globalThis.window !== 'undefined' ? (localStorage.getItem('lang') || navigator.language || 'pt') : 'pt';
      const h2 = config.headers instanceof AxiosHeaders ? config.headers : AxiosHeaders.from(config.headers as any);
      if (!h2.has('Accept-Language')) h2.set('Accept-Language', lang);
      config.headers = h2;
    } catch {}
    console.log(`[API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

/** Interceptor de response:
 *  - Em 401 (fora de /auth/login e /auth/refresh), tenta refresh com fila
 */
api.interceptors.response.use(
  (res) => {
    console.log(`[API] Response ${res.status} from ${res.config.url}`);
    return res;
  },
  async (error) => {
    console.error('[API] Response error:', {
      message: error.message,
      status: error.response?.status,
      url: error.config?.url,
      data: error.response?.data
    });
    const original: any = error.config || {};
    const status: number | undefined = error?.response?.status;
    const url: string = original?.url || "";
    const isAuthPath = url.includes("/auth/login") || url.includes("/auth/refresh");

    // Retry único para erros de rede/timeout (Render cold start)
    const isNetworkOrTimeout = !status || error.code === 'ECONNABORTED' || error.message === 'Network Error';
    if (isNetworkOrTimeout && !original._netRetry) {
      original._netRetry = true;
      try {
        await new Promise((r) => setTimeout(r, 1500));
        console.warn('[API] Retrying once after network/timeout error:', url);
        return api(original);
      } catch {}
    }

    if (status === 401 && !isAuthPath && !original._retry) {
      original._retry = true;

      // Se já há refresh a decorrer, aguarda
      if (isRefreshing) {
        const token = await new Promise<string | null>((resolve) => queue.push(resolve));
        original.headers = ensureAuthHeader(original.headers, token ?? undefined);
        return api(original);
      }

      // Inicia refresh
      isRefreshing = true;
      try {
        const refresh = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
        if (!refresh) throw new Error("no refresh token");

        // Faz refresh com header explícito (não é pisado pelo request interceptor)
        const { data } = await api.post("/auth/refresh", null, {
          headers: { Authorization: `Bearer ${refresh}` },
        });

        // Guarda novos tokens
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", data.access_token);
          if (data.refresh_token) localStorage.setItem("refresh_token", data.refresh_token);
        }

        // Desbloqueia fila
        queue.forEach((fn) => fn(data.access_token));
        queue = [];

        // Reenvia original com novo access token
        original.headers = ensureAuthHeader(original.headers, data.access_token);
        return api(original);
      } catch (e) {
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

    return Promise.reject(error);
  }
);

export default api;
