// Garante tipos do Vite
/// <reference types="vite/client" />

const RAW = import.meta.env.VITE_API_BASE || "";
// Remove barra no fim ("/") para normalizar
export const API_BASE = RAW.replace(/\/+$/, "");

// Helper básico para chamadas à API
export async function api<T = unknown>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const url = path.startsWith("/") ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
    ...init,
  });

  if (!res.ok) {
    // Tenta ler mensagem de erro do backend
    let msg = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      msg = (data?.message || data?.error || msg) as string;
    } catch {}
    throw new Error(msg);
  }

  // Alguns endpoints podem não devolver JSON (ex.: 204)
  const text = await res.text();
  return (text ? JSON.parse(text) : null) as T;
}
