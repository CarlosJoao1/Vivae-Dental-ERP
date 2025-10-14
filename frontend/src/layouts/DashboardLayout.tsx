import { Outlet, Link, useLocation } from 'react-router-dom';
import Topbar from '@/components/Topbar';

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
        {/* Use Topbar with greeting, language and tenant selector */}
        <Topbar />
        <main className="p-4"><Outlet /></main>
      </div>
    </div>
  );
}
