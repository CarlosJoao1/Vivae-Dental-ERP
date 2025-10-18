import React from 'react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const nav = [
  { to:'/', labelKey:'dashboard', icon:'🏠' },
  { to:'/masterdata', labelKey:'master_data', icon:'�' },
  { to:'/crm', labelKey:'crm', icon:'🤝' }
]

export default function Sidebar(){
  const { t } = useTranslation()
  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 overflow-y-auto border-r bg-white dark:bg-gray-900 dark:border-gray-800">
      <div className="p-4 flex items-center gap-3">
        <img src="/assets/logos/vivae-erp-logo-main.svg" alt="VIVAE ERP" className="h-8 w-auto" />
        <span className="text-xl font-bold">VIVAE ERP</span>
      </div>
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
