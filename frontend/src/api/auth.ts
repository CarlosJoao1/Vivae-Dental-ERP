// src/api/auth.ts
import api from "@/api/api";

/** POST /auth/login */
export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login", { username, password });
  return data;
}

/** POST /auth/refresh  — envia o refresh no header Authorization */
export async function refreshWithHeader(refreshToken: string) {
  const { data } = await api.post("/auth/refresh", null, {
    headers: { Authorization: `Bearer ${refreshToken}` },
  });
  return data;
}

/** GET /auth/me  — opcionalmente aceita accessToken explícito */
export async function me(accessToken?: string) {
  const { data } = await api.get("/auth/me", {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
  });
  return data;
}
