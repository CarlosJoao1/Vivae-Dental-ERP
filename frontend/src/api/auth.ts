// src/api/auth.ts
import api from "@/api/api";

/** POST /auth/login */
export async function login(username: string, password: string) {
  const r = await api.post("/auth/login", { username, password });
  return r.data;
}

/** POST /auth/refresh */
export async function refresh(refresh_token: string) {
  const r = await api.post("/auth/refresh", { refresh_token });
  return r.data;
}

/** GET /auth/me  (usa Bearer no header) */
export async function me(accessToken: string) {
  const r = await api.get("/auth/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return r.data;
}
