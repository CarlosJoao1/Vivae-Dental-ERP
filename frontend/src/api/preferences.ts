import api from "@/api/api";

export type Preferences = Record<string, any>;

export async function getPreferences() {
  const { data } = await api.get("/auth/preferences");
  return data?.preferences as Preferences || {};
}

export async function updatePreferences(preferences: Preferences) {
  const { data } = await api.put("/auth/preferences", { preferences });
  return data?.preferences as Preferences || {};
}
