import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { AuthAPI } from "@/api/api";

type User = {
  id?: string;
  username?: string;
  roles?: string[];
  tenantId?: string;
  [k: string]: any;
};

type AuthContextType = {
  loading: boolean;
  user: User | null;
  accessToken: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  authRequest: <T>(fn: (token: string) => Promise<T>) => Promise<T>;
};

const AuthContext = createContext<AuthContextType | null>(null);

const LS_ACCESS = "access_token";
const LS_REFRESH = "refresh_token";

/** Decodifica JWT sem validar assinatura, só para ler o payload (exp). */
function decodeJwt<T = any>(token: string | null): (T & { exp?: number }) | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const json = atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decodeURIComponent(escape(json)));
  } catch {
    try {
      // fallback para ambientes sem escape/unescape
      return JSON.parse(atob(parts[1]));
    } catch {
      return null;
    }
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(() => localStorage.getItem(LS_ACCESS));
  const [refreshToken, setRefreshToken] = useState<string | null>(() => localStorage.getItem(LS_REFRESH));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

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
    // Backend pode aceitar refresh no body (modelo atual do nosso api.ts)
    const res = await AuthAPI.refresh(refreshToken);
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
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    if (hard) {
      // redireciono só se o router estiver ativo na página de login; opcional
      // window.location.href = "/login";
    }
  }, []);

  /** Login + carregar /auth/me */
  const login = useCallback(async (username: string, password: string) => {
    setLoading(true);
    try {
      const res = await AuthAPI.login(username, password);
      const acc = res?.access_token;
      const ref = res?.refresh_token;
      if (!acc || !ref) throw new Error("Credenciais inválidas (tokens não recebidos)");
      localStorage.setItem(LS_ACCESS, acc);
      localStorage.setItem(LS_REFRESH, ref);
      setAccessToken(acc);
      setRefreshToken(ref);
      // tenta carregar o utilizador
      try {
        const me = await AuthAPI.me(acc);
        setUser(me?.user ?? me ?? { username });
      } catch {
        // se /me falhar, mantemos tokens mas user nulo
        setUser({ username });
      }
      scheduleRefresh();
    } finally {
      setLoading(false);
    }
  }, [scheduleRefresh]);

  /** Wrapper para chamadas autenticadas com retry em 401 */
  const authRequest = useCallback(
    async <T,>(fn: (token: string) => Promise<T>): Promise<T> => {
      if (!accessToken) throw new Error("Não autenticado.");
      try {
        return await fn(accessToken);
      } catch (err: any) {
        // tenta refresh só se 401 (quando usares fetch puro, podes propagar o status)
        const needsRetry =
          err?.message?.includes("401") ||
          err?.message?.toLowerCase?.().includes("unauthorized") ||
          err?.status === 401;
        if (!needsRetry) throw err;
        const newToken = await doRefresh();
        return fn(newToken);
      }
    },
    [accessToken, doRefresh]
  );

  /** Carrega /auth/me no arranque se houver token */
  useEffect(() => {
    (async () => {
      if (!accessToken) {
        setLoading(false);
        return;
      }
      try {
        const me = await AuthAPI.me(accessToken);
        setUser(me?.user ?? me ?? null);
      } catch {
        // access inválido → tenta refresh
        try {
          const newAcc = await doRefresh();
          const me2 = await AuthAPI.me(newAcc);
          setUser(me2?.user ?? me2 ?? null);
        } catch {
          doLogout(false);
        }
      } finally {
        setLoading(false);
      }
    })();
    // limpar timer ao desmontar
    return () => clearTimer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      loading,
      user,
      accessToken,
      login,
      logout: doLogout,
      authRequest,
    }),
    [loading, user, accessToken, login, doLogout, authRequest]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
