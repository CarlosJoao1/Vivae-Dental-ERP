
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '@/api/api';
type Tenant = { id: string; name: string };
export default function Dashboard() {
  const { t } = useTranslation();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [activeUsers, setActiveUsers] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { 
    let cancelled = false
    const load = async () => {
      setLoading(true)
      try {
        // /api/tenants devolve um ARRAY simples
        const ten = await api.get('/tenants');
        if (cancelled) return
        const items: Tenant[] = Array.isArray(ten.data) ? ten.data : (ten.data?.tenants || []);
        setTenants(items || []);
        // /api/auth/stats devolve métricas para o dashboard
        const st = await api.get('/auth/stats');
        if (cancelled) return
        const au = st?.data?.users_in_tenant;
        setActiveUsers(typeof au === 'number' ? au : null);
      } catch (e: any) {
        if (cancelled) return
        setError(e?.response?.data?.error || e?.message || 'Erro a carregar dados');
      } finally { if (!cancelled) setLoading(false); }
    }
    load()
    const handler = () => load()
    window.addEventListener('tenant:changed', handler)
    return () => { cancelled = true; window.removeEventListener('tenant:changed', handler) }
  }, []);
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      {loading && <div className="card">A carregar…</div>}
      {error && <div className="card bg-red-50 text-red-700">{error}</div>}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card hover:shadow-md transition cursor-pointer">
          <div className="text-sm text-gray-500">Tenants</div>
          <div className="text-3xl font-bold">{tenants.length}</div>
          <div className="text-xs text-gray-500 mt-1">Laboratórios disponíveis</div>
        </div>
        <div className="card hover:shadow-md transition cursor-pointer">
          <div className="text-sm text-gray-500">Utilizadores ativos</div>
          <div className="text-3xl font-bold">{activeUsers != null ? activeUsers : '—'}</div>
          <div className="text-xs text-gray-500 mt-1">no laboratório ativo</div>
        </div>
      </section>
      <section className="card">
        <div className="flex items-center justify-between mb-3"><h2 className="text-lg font-semibold">Laboratórios</h2></div>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead><tr className="text-left text-sm text-gray-600"><th className="py-2">Nome</th><th className="py-2">ID</th></tr></thead>
            <tbody>
              {tenants.map(t => (<tr key={t.id} className="border-t"><td className="py-2">{t.name}</td><td className="py-2 text-gray-500">{t.id}</td></tr>))}
              {tenants.length === 0 && !loading && (<tr><td className="py-2 text-gray-500" colSpan={2}>Sem dados</td></tr>)}
            </tbody>
          </table>
        </div>
      </section>

      {/* Nova seção de módulos */}
      <section className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{t('modules')}</h2>
          <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
            {t('under_development')}
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { key: 'financial_management', icon: '💰', color: 'bg-green-50 border-green-200' },
            { key: 'purchasing', icon: '🛒', color: 'bg-blue-50 border-blue-200' },
            { key: 'warehouse', icon: '📦', color: 'bg-purple-50 border-purple-200' },
            { key: 'projects', icon: '📋', color: 'bg-yellow-50 border-yellow-200' },
            { key: 'resource_planning', icon: '📊', color: 'bg-indigo-50 border-indigo-200' },
            { key: 'service', icon: '🔧', color: 'bg-red-50 border-red-200' },
            { key: 'human_resources', icon: '👥', color: 'bg-teal-50 border-teal-200' },
            { key: 'integrations', icon: '🔌', color: 'bg-pink-50 border-pink-200' },
            { key: 'administration', icon: '⚙️', color: 'bg-gray-50 border-gray-200' },
            { key: 'quality', icon: '✅', color: 'bg-emerald-50 border-emerald-200' },
            { key: 'document_capture', icon: '📄', color: 'bg-cyan-50 border-cyan-200' }
          ].map(module => (
            <div key={module.key} className={`p-4 rounded-lg border-2 ${module.color} opacity-75 cursor-not-allowed`}>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{module.icon}</span>
                <h3 className="font-medium text-gray-800">{t(module.key)}</h3>
              </div>
              <div className="text-xs text-gray-600 bg-white bg-opacity-60 px-2 py-1 rounded">
                {t('status_dev_license')}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
