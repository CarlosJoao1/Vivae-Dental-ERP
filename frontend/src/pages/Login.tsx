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
    <div className="min-h-screen grid place-items-center bg-gray-50 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm bg-white p-6 rounded-xl shadow">
        <h1 className="text-xl font-semibold mb-4">Entrar</h1>
        {err && <div className="bg-red-100 text-red-700 p-2 rounded mb-3">{err}</div>}
        <label className="block text-sm mb-1">Utilizador</label>
        <input value={username} onChange={(e) => setU(e.target.value)} className="input w-full mb-3" />
        <label className="block text-sm mb-1">Senha</label>
        <input type="password" value={password} onChange={(e) => setP(e.target.value)} className="input w-full mb-4" />
        <button disabled={loading} className="btn btn-primary w-full">
          {loading ? "A entrar…" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
