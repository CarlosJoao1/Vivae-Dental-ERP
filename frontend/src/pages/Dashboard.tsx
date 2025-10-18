
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
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
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      {loading && <div className="card">A carregar…</div>}
      {error && <div className="card bg-red-50 text-red-700">{error}</div>}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="card hover:shadow-md transition cursor-pointer p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Empresas</div>
          <div className="text-2xl font-bold mt-1">{tenants.length}</div>
          <div className="text-xs text-gray-500 mt-1">disponíveis no sistema</div>
        </div>
        <div className="card hover:shadow-md transition cursor-pointer p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Utilizadores Ativos</div>
          <div className="text-2xl font-bold mt-1">{activeUsers != null ? activeUsers : '—'}</div>
          <div className="text-xs text-gray-500 mt-1">na empresa ativa</div>
        </div>
      </section>

      {/* Nova seção de funcionalidades */}
      <section className="card p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold">{t('features')}</h2>
          <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
            {t('under_development')}
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { key: 'master_data', icon: '📊', color: 'bg-purple-50 border-purple-200 hover:bg-purple-100', url: 'masterdata', isFunctional: true },
            { key: 'sales_module', icon: '💰', color: 'bg-green-50 border-green-200 hover:bg-green-100', url: 'sales', isFunctional: true },
            { key: 'crm_module', icon: '🤝', color: 'bg-blue-50 border-blue-200 hover:bg-blue-100', url: 'crm', isFunctional: true },
            { key: 'production', icon: '🏭', color: 'bg-orange-50 border-orange-200 hover:bg-orange-100', url: 'production', isFunctional: true },
            { key: 'financial_management', icon: '💵', color: 'bg-emerald-50 border-emerald-200 hover:bg-emerald-100', url: 'financial-management' },
            { key: 'purchasing', icon: '🛒', color: 'bg-indigo-50 border-indigo-200 hover:bg-indigo-100', url: 'purchasing' },
            { key: 'warehouse', icon: '📦', color: 'bg-purple-50 border-purple-200 hover:bg-purple-100', url: 'warehouse' },
            { key: 'projects', icon: '📋', color: 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100', url: 'projects' },
            { key: 'resource_planning', icon: '📊', color: 'bg-cyan-50 border-cyan-200 hover:bg-cyan-100', url: 'resource-planning' },
            { key: 'service', icon: '🔧', color: 'bg-red-50 border-red-200 hover:bg-red-100', url: 'service' },
            { key: 'human_resources', icon: '👥', color: 'bg-teal-50 border-teal-200 hover:bg-teal-100', url: 'human-resources' },
            { key: 'integrations', icon: '🔌', color: 'bg-pink-50 border-pink-200 hover:bg-pink-100', url: 'integrations' },
            { key: 'administration', icon: '⚙️', color: 'bg-gray-50 border-gray-200 hover:bg-gray-100', url: 'administration' },
            { key: 'quality', icon: '✅', color: 'bg-lime-50 border-lime-200 hover:bg-lime-100', url: 'quality' },
            { key: 'document_capture', icon: '📄', color: 'bg-sky-50 border-sky-200 hover:bg-sky-100', url: 'document-capture' }
          ].map(module => (
            <Link 
              key={module.key} 
              to={module.isFunctional ? `/${module.url}` : `/module/${module.url}`}
              className={`p-4 rounded-lg border-2 ${module.color} transition-all duration-200 cursor-pointer block`}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{module.icon}</span>
                <h3 className="font-medium text-gray-800">{t(module.key)}</h3>
              </div>
              {!module.isFunctional && (
                <div className="text-xs text-gray-600 bg-white bg-opacity-60 px-2 py-1 rounded">
                  {t('status_dev_license')}
                </div>
              )}
            </Link>
          ))}
        </div>
      </section>

      {/* Seção de Empresas movida para baixo */}
      <section className="card p-4">
        <div className="flex items-center justify-between mb-3"><h2 className="text-base font-semibold">Empresas</h2></div>
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
    </div>
  );
}
