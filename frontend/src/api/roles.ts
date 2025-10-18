import api from "@/api/api";

export type Feature = { key: string; label: string; actions: string[] };
export type Policies = Record<string, Record<string, Record<string, boolean>>>; // role -> feature -> action -> allowed

export async function listFeatures() {
  const { data } = await api.get("/roles/features");
  return data as { items: Feature[] };
}

export async function getPolicies() {
  const { data } = await api.get("/roles/policies");
  return data as { lab_id: string; policies: Policies };
}

export async function updatePolicies(policies: Policies) {
  const { data } = await api.put("/roles/policies", { policies });
  return data as { ok: boolean };
}
