import React, { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import LanguageSwitcher from './LanguageSwitcher'
import ThemeToggle from './ThemeToggle'
import { useTranslation } from 'react-i18next'
import api from '@/api/api'

export default function Topbar(){
  const { user, logout, tenants, tenantId, setTenant } = useAuth()
  const { t, i18n } = useTranslation()
  // Normaliza idioma para código de 2 letras (ex.: 'pt-PT' -> 'PT')
  const lang = ((i18n.language || 'pt').split('-')[0] || 'pt').toUpperCase()
  const [version, setVersion] = useState<string | null>(null)
  useEffect(() => {
    let mounted = true
    api.get('/health/info')
      .then((res) => {
        if (!mounted) return
        const v = res.data?.version as string | undefined
        if (v) setVersion(v)
      })
      .catch(() => {
        // silencioso, não crítico
      })
    return () => { mounted = false }
  }, [])
  return (
    <header className="w-full border-b bg-white/70 dark:bg-gray-900/70 backdrop-blur sticky top-0 z-10">
      <div className="h-14 px-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {version && (
            <span className="text-xs rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 px-2 py-0.5">{version}</span>
          )}
          <input placeholder={t('search') as string} className="px-3 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-800 min-w-[240px]" />
          <select className="px-2 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-800" value={tenantId || ''} onChange={(e)=>setTenant(e.target.value)}>
            {(tenants||[]).map(tn => (<option key={tn.id} value={tn.id}>{tn.name}</option>))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          {/* Saudação no canto superior direito */}
          <span className="text-sm font-medium text-gray-700 dark:text-gray-200 mr-2">
            {t('Bem-vindo')}, {user?.username || 'user'} ({lang})
          </span>
          <LanguageSwitcher />
          <ThemeToggle />
          <button onClick={logout} className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('logout')}</button>
        </div>
      </div>
    </header>
  )
}
