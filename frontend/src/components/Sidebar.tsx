import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

interface NavItem {
  path: string
  icon: string
  label: string
  licensed: boolean
}

export default function Sidebar(){
  const { t } = useTranslation()
  const location = useLocation()

  const navItems: NavItem[] = [
    { path: '/', icon: '🏠', label: t('dashboard') || 'Dashboard', licensed: true },
    { path: '/crm', icon: '👥', label: t('crm') || 'CRM', licensed: true },
    { path: '/production', icon: '🏭', label: t('production') || 'Produção', licensed: true },
    { path: '/sales', icon: '💰', label: t('sales') || 'Vendas', licensed: false },
    { path: '/inventory', icon: '📦', label: t('inventory') || 'Inventário', licensed: false },
    { path: '/purchases', icon: '🛒', label: t('purchases') || 'Compras', licensed: false },
    { path: '/finance', icon: '💳', label: t('finance') || 'Financeiro', licensed: false },
  ]

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 overflow-y-auto border-r bg-white dark:bg-gray-900 dark:border-gray-800">
      {/* Logo */}
      <Link 
        to="/" 
        className="p-4 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border-b dark:border-gray-800"
      >
        <img src="/assets/logos/vivae-erp-logo-main.svg" alt="VIVAE ERP" className="h-8 w-auto" />
        <span className="text-xl font-bold">VIVAE ERP</span>
      </Link>

      {/* Navigation */}
      <nav className="p-2 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`
              flex items-center gap-3 px-3 py-2 rounded-lg transition-colors
              ${isActive(item.path) 
                ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300' 
                : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800'
              }
              ${!item.licensed ? 'opacity-50' : ''}
            `}
          >
            <span className="text-xl">{item.icon}</span>
            <span className="flex-1 font-medium">{item.label}</span>
            {!item.licensed && (
              <span className="text-xs bg-gray-200 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                🔒
              </span>
            )}
          </Link>
        ))}
      </nav>

      {/* Production Sub-Menu (if in production section) */}
      {location.pathname.startsWith('/production') && (
        <div className="px-2 pb-2">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 px-3 py-2 uppercase tracking-wider">
            {t('production_menu') || 'Produção'}
          </div>
          <div className="space-y-1">
            <Link
              to="/production/design"
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              <span>🎨</span> {t('product_design') || 'Design de Produtos'}
            </Link>
            <Link
              to="/production/capabilities"
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              <span>⚡</span> {t('capabilities') || 'Capacidades'}
            </Link>
            <Link
              to="/production/planning"
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              <span>📅</span> {t('planning') || 'Planeamento'}
            </Link>
            <Link
              to="/production/execution"
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              <span>🔨</span> {t('execution') || 'Execução'}
            </Link>
            <Link
              to="/production/costing"
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              <span>💰</span> {t('costing') || 'Custeio'}
            </Link>
            <Link
              to="/production/tasks"
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              <span>✅</span> {t('tasks') || 'Tarefas'}
            </Link>
            <Link
              to="/production/admin"
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              <span>⚙️</span> {t('production_admin') || 'Administração'}
            </Link>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          <div className="font-semibold">Vivae Dental Lab</div>
          <div className="mt-1">
            License: {t('valid_until') || 'Válida até'} 2027-12-31
          </div>
        </div>
      </div>
    </aside>
  )
}
