import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  const from = (location.state as any)?.from?.pathname || "/";

  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      await login(username, password);
      nav(from, { replace: true });
    } catch (e: any) {
      setErr(e?.message || "Falha no login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 px-4">
      <div className="w-full max-w-md">
        {/* Logo and Title Card */}
        <div className="text-center mb-8 animate-fadeIn">
          <div className="flex items-center justify-center gap-3 mb-4">
            <img 
              src="/assets/logos/vivae-erp-logo-main.svg" 
              alt="VIVAE ERP" 
              className="h-12 w-auto transition-transform duration-300 hover:scale-110" 
            />
            <span className="text-3xl font-bold text-gray-800 dark:text-gray-100">VIVAE ERP</span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">Sistema de Gestão Laboratorial</p>
        </div>

        {/* Login Form Card */}
        <form 
          onSubmit={onSubmit} 
          className="bg-white dark:bg-gray-900 p-8 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-3xl"
        >
          <h1 className="text-2xl font-semibold mb-6 text-gray-900 dark:text-gray-100">Bem-vindo</h1>
          
          {err && (
            <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 p-4 rounded-lg mb-6 border border-red-200 dark:border-red-800 animate-shake">
              <div className="flex items-center gap-2">
                <span className="text-lg">⚠️</span>
                <span className="text-sm font-medium">{err}</span>
              </div>
            </div>
          )}
          
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Utilizador</label>
              <input 
                value={username} 
                onChange={(e) => setU(e.target.value)} 
                className="input w-full transition-all duration-200 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400" 
                placeholder="Digite seu utilizador"
                autoComplete="username"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Senha</label>
              <input 
                type="password" 
                value={password} 
                onChange={(e) => setP(e.target.value)} 
                className="input w-full transition-all duration-200 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400" 
                placeholder="Digite sua senha"
                autoComplete="current-password"
              />
            </div>
          </div>
          
          <button 
            disabled={loading} 
            className="btn btn-primary w-full mt-8 py-3 text-base font-semibold transition-all duration-200 hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                A entrar…
              </span>
            ) : (
              "Entrar"
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="text-center mt-6 text-xs text-gray-500 dark:text-gray-400">
          © 2025 VIVAE ERP. Todos os direitos reservados.
        </div>
      </div>
    </div>
  );
}
