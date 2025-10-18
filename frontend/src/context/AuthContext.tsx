// import AuthAPI from "@/api/api";
import { login as authLogin, refreshWithHeader as authRefresh, me as authMe } from "@/api/auth";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import AuthAPI from "@/api/api"; // <-- default import para corrigir TS2614
import { getPreferences as apiGetPrefs, updatePreferences as apiUpdatePrefs } from "@/api/preferences";


// Tipos
export type Tenant = { id?: string; _id?: string; name?: string };

type User = {
  id?: string;
  username?: string;
  roles?: string[];
  tenantId?: string;
  tenants?: Tenant[]; // caso venha no payload do /me
  [k: string]: any;
};

type AuthContextType = {
  loading: boolean;
  user: User | null;
  accessToken: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  authRequest: <T>(fn: (token: string) => Promise<T>) => Promise<T>;

  // --- Multi-tenant exposto ao Topbar ---
  tenants: Tenant[];
  tenantId: string | null;
  setTenant: (tenantId: string) => void;

  // User Preferences
  preferences: Record<string, any>;
  setPreference: (key: string, value: any) => Promise<void>;
};

// Contexto
const AuthContext = createContext<AuthContextType | null>(null);

// LocalStorage keys
const LS_ACCESS = "access_token";
const LS_REFRESH = "refresh_token";
const LS_TENANT = "tenant_id";

/** Decodifica JWT (sem validar assinatura) para ler `exp`. */
function decodeJwt<T = any>(token: string | null): (T & { exp?: number }) | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
  try {
    // Browser
    const json = atob(b64);
    return JSON.parse(decodeURIComponent(escape(json)));
  } catch {
    try {
      // Node/SSR fallback
      const json = Buffer.from(b64, "base64").toString("utf8");
      return JSON.parse(json);
    } catch {
      return null;
    }
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(() =>
    localStorage.getItem(LS_ACCESS),
  );
  const [refreshToken, setRefreshToken] = useState<string | null>(() =>
    localStorage.getItem(LS_REFRESH),
  );
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // --- Multi-tenant ---
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(() => localStorage.getItem(LS_TENANT));
  const [preferences, setPreferences] = useState<Record<string, any>>({});

  // timer para refresh automático
  const refreshTimer = useRef<number | null>(null);

  const clearTimer = () => {
    if (refreshTimer.current) {
      window.clearTimeout(refreshTimer.current);
      refreshTimer.current = null;
    }
  };

  /** Agenda refresh ~60s antes do expirar do accessToken (se houver exp). */
  const scheduleRefresh = useCallback(() => {
    clearTimer();
    const payload = decodeJwt(accessToken);
    if (!payload?.exp) return; // sem exp => não agenda
    const expMs = payload.exp * 1000;
    const now = Date.now();
    // refrescar 60s antes de expirar, mínimo 5s
    const delay = Math.max(expMs - now - 60_000, 5_000);
    refreshTimer.current = window.setTimeout(async () => {
      try {
        await doRefresh();
      } catch {
        // se falhar refresh, forçamos logout silencioso
        doLogout(false);
      }
    }, delay) as unknown as number;
  }, [accessToken, refreshToken]);

  /** Faz refresh via API e atualiza estado/localStorage. */
  const doRefresh = useCallback(async () => {
    if (!refreshToken) throw new Error("No refresh token");
    // const res = await AuthAPI.refresh(refreshToken);
    const res = await authRefresh(refreshToken);
    const newAccess = res?.access_token;
    const newRefresh = res?.refresh_token ?? refreshToken; // alguns backends não devolvem novo refresh
    if (!newAccess) throw new Error("No access token from refresh");

    localStorage.setItem(LS_ACCESS, newAccess);
    localStorage.setItem(LS_REFRESH, newRefresh);
    setAccessToken(newAccess);
    setRefreshToken(newRefresh);
    scheduleRefresh();
    return newAccess;
  }, [refreshToken, scheduleRefresh]);

  /** Logout + limpeza */
  const doLogout = useCallback((hard: boolean = true) => {
    clearTimer();
    localStorage.removeItem(LS_ACCESS);
    localStorage.removeItem(LS_REFRESH);
    localStorage.removeItem(LS_TENANT);
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    setTenants([]);
    setTenantId(null);
    if (hard) {
      // opcional: redirecionar para /login
      // window.location.href = "/login";
    }
  }, []);

  /** Helper: escolher tenantId a partir dos dados recebidos */
  const pickTenantId = (me: User | null, list: Tenant[]): string | null => {
    const candidate =
      me?.tenantId ||
      (list[0]?.id as string | undefined) ||
      (list[0]?._id as string | undefined) ||
      null;
    return candidate ?? null;
  };

  /** Login + carregar /auth/me */
  const login = useCallback(
    async (username: string, password: string) => {
      setLoading(true);
      try {
        //const res = await AuthAPI.login(username, password);
        const res = await authLogin(username, password);
        const acc = res?.access_token;
        const ref = res?.refresh_token;
        if (!acc || !ref) throw new Error("Credenciais inválidas (tokens não recebidos)");
        localStorage.setItem(LS_ACCESS, acc);
        localStorage.setItem(LS_REFRESH, ref);
        setAccessToken(acc);
        setRefreshToken(ref);

        // tenta carregar o utilizador
        let me: User | null = null;
        try {
          //const meResp = await AuthAPI.me(acc);
          const meResp = await authMe(acc);
          me = (meResp?.user ?? meResp ?? null) as User | null;
          setUser(me ?? { username });
        } catch {
          setUser({ username });
        }

        // multi-tenant
        const ts: Tenant[] =
          (res?.tenants as Tenant[] | undefined) ||
          (me?.tenants as Tenant[] | undefined) ||
          [];
        setTenants(ts);
        const chosen = pickTenantId(me, ts);
        if (chosen) {
          setTenantId(chosen);
          localStorage.setItem(LS_TENANT, chosen);
        }

        // Load user preferences
        try {
          const prefs = await apiGetPrefs();
          setPreferences(prefs || {});
        } catch {}

        scheduleRefresh();
      } finally {
        setLoading(false);
      }
    },
    [scheduleRefresh],
  );

  /** Wrapper para chamadas autenticadas com retry em 401 */
  const authRequest = useCallback(
    async <T,>(fn: (token: string) => Promise<T>): Promise<T> => {
      if (!accessToken) throw new Error("Não autenticado.");
      try {
        return await fn(accessToken);
      } catch (err: any) {
        const needsRetry =
          err?.message?.includes("401") ||
          err?.message?.toLowerCase?.().includes("unauthorized") ||
          err?.status === 401;
        if (!needsRetry) throw err;
        const newToken = await doRefresh();
        return fn(newToken);
      }
    },
    [accessToken, doRefresh],
  );

  /** Carrega /auth/me no arranque se houver token */
  useEffect(() => {
    (async () => {
      if (!accessToken) {
        setLoading(false);
        return;
      }
      try {
        //const meResp = await AuthAPI.me(accessToken);
        const meResp = await authMe(accessToken);
        const me = (meResp?.user ?? meResp ?? null) as User | null;
        setUser(me);

        // multi-tenant na inicialização
  const ts: Tenant[] = (me?.tenants as Tenant[] | undefined) ?? [];
        setTenants(ts);

        const stored = localStorage.getItem(LS_TENANT);
        const validStored =
          stored && ts.some((t) => (t.id ?? t._id) === stored) ? stored : null;

        const chosen = validStored ?? pickTenantId(me, ts);
        if (chosen) {
          setTenantId(chosen);
          localStorage.setItem(LS_TENANT, chosen);
        } else {
          setTenantId(null);
          localStorage.removeItem(LS_TENANT);
        }
        // Load preferences after successful /me
        try {
          const prefs = await apiGetPrefs();
          setPreferences(prefs || {});
        } catch {}
      } catch {
        // access inválido → tenta refresh
        try {
          const newAcc = await doRefresh();
          //const me2Resp = await AuthAPI.me(newAcc);
          const me2Resp = await authMe(newAcc);
          const me2 = (me2Resp?.user ?? me2Resp ?? null) as User | null;
          setUser(me2);

          const ts: Tenant[] = (me2?.tenants as Tenant[] | undefined) ?? [];
          setTenants(ts);

          const stored = localStorage.getItem(LS_TENANT);
          const validStored =
            stored && ts.some((t) => (t.id ?? t._id) === stored) ? stored : null;

          const chosen = validStored ?? pickTenantId(me2, ts);
          if (chosen) {
            setTenantId(chosen);
            localStorage.setItem(LS_TENANT, chosen);
          } else {
            setTenantId(null);
            localStorage.removeItem(LS_TENANT);
          }
          try {
            const prefs2 = await apiGetPrefs();
            setPreferences(prefs2 || {});
          } catch {}
        } catch {
          doLogout(false);
        }
      } finally {
        setLoading(false);
      }
    })();
    return () => clearTimer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // setter público de tenant
  const setTenant = useCallback((id: string) => {
    setTenantId(id);
    localStorage.setItem(LS_TENANT, id);
    // Notify app to refresh data for the new tenant
    try {
      const ev = new CustomEvent('tenant:changed', { detail: { tenantId: id } });
      window.dispatchEvent(ev);
    } catch {}
  }, []);

  // Persist a single preference key
  const setPreference = useCallback(async (key: string, value: any) => {
    const next = { ...preferences, [key]: value };
    setPreferences(next);
    try {
      await apiUpdatePrefs(next);
    } catch {
      // ignore persistence error for now
    }
  }, [preferences]);

  const value = useMemo<AuthContextType>(
    () => ({
      loading,
      user,
      accessToken,
      login,
      logout: doLogout,
      authRequest,
      tenants,
      tenantId,
      setTenant,
      preferences,
      setPreference,
    }),
    [loading, user, accessToken, login, doLogout, authRequest, tenants, tenantId, setTenant, preferences, setPreference],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
