
import { createContext, useContext, useMemo, useState, useEffect } from 'react';
import api from '@/api/api';
type AuthCtx = { access: string | null; login: (u: string, p: string) => Promise<void>; logout: () => void; };
const AuthContext = createContext<AuthCtx | null>(null);
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [access, setAccess] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [_refresh, setRefresh] = useState<string | null>(() => localStorage.getItem('refresh_token'));
  useEffect(() => { if (!access) return; /* api.get('/auth/me').catch(() => logout()); */ }, [access]);
  const login = async (username: string, password: string) => {
    const { data } = await api.post('/auth/login', { username, password });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setAccess(data.access_token); setRefresh(data.refresh_token);
  };
  const logout = () => { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); setAccess(null); setRefresh(null); };
  const value = useMemo(() => ({ access, login, logout }), [access]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const ctx = useContext(AuthContext); if (!ctx) throw new Error('useAuth must be used within AuthProvider'); return ctx; }
