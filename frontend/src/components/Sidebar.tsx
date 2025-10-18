import React from 'react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const nav = [
  { to:'/dashboard', labelKey:'dashboard', icon:'🏠' },
  { to:'/modules/billing', labelKey:'billing', icon:'💳' },
  { to:'/modules/production', labelKey:'production', icon:'🏭' },
  { to:'/modules/purchases', labelKey:'purchases', icon:'🧾' },
  { to:'/modules/hr', labelKey:'hr', icon:'👥' },
  { to:'/modules/finance', labelKey:'finance', icon:'💼' },
  { to:'/modules/inventory', labelKey:'inventory', icon:'📦' },
  { to:'/modules/crm', labelKey:'crm', icon:'🤝' },
  { to:'/modules/mes', labelKey:'mes', icon:'🧩' },
  { to:'/modules/dispatch', labelKey:'dispatch', icon:'📤' },
  { to:'/modules/webservices', labelKey:'webservices', icon:'🔗' },
  { to:'/modules/sequencing', labelKey:'sequencing', icon:'🗂️' },
  { to:'/modules/labeling', labelKey:'labeling', icon:'🏷️' }
]

export default function Sidebar(){
  const { t } = useTranslation()
  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 overflow-y-auto border-r bg-white dark:bg-gray-900 dark:border-gray-800">
      <div className="p-4 text-xl font-bold">VIVAE ERP</div>
      <nav className="px-2 pb-6">
        {nav.map(item => (
          <NavLink key={item.to} to={item.to}
            className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-md mb-1 ${isActive? 'bg-blue-600 text-white' : 'hover:bg-gray-100 dark:hover:bg-gray-800'}`}>
            <span className="text-lg">{item.icon}</span>
            <span>{t(item.labelKey)}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
