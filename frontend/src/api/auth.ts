import api from "@/api/api";

export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login", { username, password });
  // guarda tokens (opcional aqui; o teu AuthContext já faz isso)
  return data;
}

export async function refreshWithHeader(refreshToken: string) {
  const { data } = await api.post("/auth/refresh", null, {
    headers: { Authorization: `Bearer ${refreshToken}` },
  });
  return data;
}

export async function me(accessToken?: string) {
  const { data } = await api.get("/auth/me", {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
  });
  return data;
}
