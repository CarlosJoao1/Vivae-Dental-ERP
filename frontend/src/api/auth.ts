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

/** POST /auth/register — create a new user, optionally tied to a lab (tenant_id) */
export async function registerUser(body: {
  username: string;
  password: string;
  email?: string;
  role?: string; // admin | manager | operator | user
  tenant_id?: string; // Laboratory id
}) {
  const { data } = await api.post("/auth/register", body);
  return data as { id: string; username: string; tenant_id?: string | null };
}

/** Sysadmin-only: list all users */
export async function listUsers() {
  const { data } = await api.get("/auth/users");
  return data as { items: Array<{ id: string; username: string; email?: string; role: string; tenant_id?: string | null; allowed_labs: string[] }> };
}

/** Sysadmin-only: update a user's allowed labs */
export async function updateUserAllowedLabs(uid: string, labIds: string[]) {
  const { data } = await api.put(`/auth/users/${uid}/allowed-labs`, { lab_ids: labIds });
  return data as { ok: boolean };
}

/** Sysadmin-only: update a user's role (cannot set to sysadmin) */
export async function updateUserRole(uid: string, role: string) {
  const { data } = await api.put(`/auth/users/${uid}/role`, { role });
  return data as { ok: boolean };
}

/** Sysadmin-only: update a user's tenant (must be within allowed_labs; empty to clear) */
export async function updateUserTenant(uid: string, tenantId?: string | null) {
  const { data } = await api.put(`/auth/users/${uid}/tenant`, { tenant_id: tenantId || "" });
  return data as { ok: boolean };
}
