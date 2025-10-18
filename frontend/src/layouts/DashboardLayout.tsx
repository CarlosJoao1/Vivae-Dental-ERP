import { Outlet, Link, useLocation } from 'react-router-dom';
import Topbar from '@/components/Topbar';
import { useTranslation } from 'react-i18next';
import React from 'react';

export default function DashboardLayout() {
  const { pathname } = useLocation();
  const { t } = useTranslation();
  const nav = [
    { to: '/', label: t('dashboard') as string },
    { to: '/masterdata', label: t('master_data') as string },
    // Produção será tratada como grupo colapsável abaixo
    { to: '/crm', label: t('crm') as string },
    // Vendas será tratado como grupo colapsável abaixo
  ];

  const [openProduction, setOpenProduction] = React.useState<boolean>(false);
  const [openSales, setOpenSales] = React.useState<boolean>(false);
  React.useEffect(() => {
    // Se o utilizador já está numa rota de produção, manter aberto
    if (pathname.startsWith('/production')) setOpenProduction(true);
    if (pathname.startsWith('/sales')) setOpenSales(true);
  }, [pathname]);
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-white border-r px-4 py-6 hidden md:block">
        <div className="flex items-center gap-3 mb-6">
          <img src="/assets/logos/vivae-erp-logo-main.svg" alt="VIVAE ERP" className="h-8 w-auto" />
          <span className="text-xl font-bold">VIVAE ERP</span>
        </div>
        <nav className="space-y-1">
          {nav.map((n) => (
            <Link key={n.to} to={n.to} className={`block px-3 py-2 rounded-lg hover:bg-gray-100 ${pathname === n.to ? 'bg-gray-100 font-semibold' : ''}`}>
              {n.label}
            </Link>
          ))}

          {/* Grupo Produção (colapsável) */}
          <button
            type="button"
            onClick={() => setOpenProduction((v) => !v)}
            className={`w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 flex items-center justify-between ${pathname.startsWith('/production') ? 'bg-gray-100 font-semibold' : ''}`}
          >
            <span>{t('production') as string}</span>
            <span>{openProduction ? '−' : '+'}</span>
          </button>
          {openProduction && (
            <div className="ml-4 space-y-1">
              <Link to={'/production/admin'} className={`block px-3 py-2 rounded-lg hover:bg-gray-100 ${pathname === '/production/admin' ? 'bg-gray-100 font-semibold' : ''}`}>
                {(t('production_admin') as string) || 'Administração'}
              </Link>
              <Link to={'/production/workcenters'} className={`block px-3 py-2 rounded-lg hover:bg-gray-100 ${pathname === '/production/workcenters' ? 'bg-gray-100 font-semibold' : ''}`}>
                {(t('work_centers') as string) || 'Centros de Trabalho'}
              </Link>
              <Link to={'/production/machines'} className={`block px-3 py-2 rounded-lg hover:bg-gray-100 ${pathname === '/production/machines' ? 'bg-gray-100 font-semibold' : ''}`}>
                {(t('machine_centers') as string) || 'Centro Máquina'}
              </Link>
            </div>
          )}

          {/* Grupo Vendas (colapsável) */}
          <button
            type="button"
            onClick={() => setOpenSales((v) => !v)}
            className={`w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 flex items-center justify-between ${pathname.startsWith('/sales') ? 'bg-gray-100 font-semibold' : ''}`}
          >
            <span>{(t('sales') as string) || 'Vendas'}</span>
            <span>{openSales ? '−' : '+'}</span>
          </button>
          {openSales && (
            <div className="ml-4 space-y-1">
              <Link to={'/sales/orders'} className={`block px-3 py-2 rounded-lg hover:bg-gray-100 ${pathname === '/sales/orders' ? 'bg-gray-100 font-semibold' : ''}`}>
                {t('sales_orders') as string}
              </Link>
              <Link to={'/sales/invoices'} className={`block px-3 py-2 rounded-lg hover:bg-gray-100 ${pathname === '/sales/invoices' ? 'bg-gray-100 font-semibold' : ''}`}>
                {t('sales_invoices') as string}
              </Link>
            </div>
          )}
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
