import React from 'react'
import { useAuth } from '@/context/AuthContext'
import LanguageSwitcher from './LanguageSwitcher'
import ThemeToggle from './ThemeToggle'
import { useTranslation } from 'react-i18next'

export default function Topbar(){
  const { user, logout, tenants, tenantId, setTenant } = useAuth()
  const { t } = useTranslation()
  return (
    <header className="w-full border-b bg-white/70 dark:bg-gray-900/70 backdrop-blur sticky top-0 z-10">
      <div className="h-14 px-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <input placeholder={t('search') as string} className="px-3 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-800 min-w-[240px]" />
          <select className="px-2 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-800" value={tenantId || ''} onChange={(e)=>setTenant(e.target.value)}>
            {(tenants||[]).map(tn => (<option key={tn.id} value={tn.id}>{tn.name}</option>))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />
          <div className="px-3 py-1 rounded bg-gray-100 dark:bg-gray-800">{user?.username || 'user'}</div>
          <button onClick={logout} className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('logout')}</button>
        </div>
      </div>
    </header>
  )
}
