
import { Outlet, Link, useLocation } from 'react-router-dom';
export default function DashboardLayout() {
  const { pathname } = useLocation();
  const nav = [
    { to: '/', label: 'Dashboard' },
    { to: '/masterdata', label: 'Master Data' },
    { to: '/production', label: 'Produção' },
    { to: '/crm', label: 'CRM' },
  ];
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-white border-r px-4 py-6 hidden md:block">
        <div className="text-xl font-bold mb-6">Vivae Dental ERP</div>
        <nav className="space-y-1">
          {nav.map((n) => (
            <Link key={n.to} to={n.to} className={`block px-3 py-2 rounded-lg hover:bg-gray-100 ${pathname === n.to ? 'bg-gray-100 font-semibold' : ''}`}>
              {n.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="flex-1 flex flex-col">
        <header className="h-14 bg-white border-b flex items-center justify-between px-4">
          <div className="md:hidden font-bold">Vivae ERP</div>
          <div className="flex items-center gap-3"><span className="badge">PT · EN · ES · FR · CN</span></div>
        </header>
        <main className="p-4"><Outlet /></main>
      </div>
    </div>
  );
}
