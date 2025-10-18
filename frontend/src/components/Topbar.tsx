import React, { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { Link } from 'react-router-dom'
import LanguageSwitcher from './LanguageSwitcher'
import ThemeToggle from './ThemeToggle'
import GlobalSearch from './GlobalSearch'
import Breadcrumbs from './Breadcrumbs'
import { useTranslation } from 'react-i18next'
import api from '@/api/api'

export default function Topbar(){
  const { user, logout, tenants, tenantId, setTenant } = useAuth()
  const { t, i18n } = useTranslation()
  // Normaliza idioma para código de 2 letras (ex.: 'pt-PT' -> 'PT')
  const lang = ((i18n.language || 'pt').split('-')[0] || 'pt').toUpperCase()
  const [version, setVersion] = useState<string | null>(null)
  const [branch, setBranch] = useState<string | null>(null)
  const [commit, setCommit] = useState<string | null>(null)
  const [buildTime, setBuildTime] = useState<string | null>(null)
  const [apiOk, setApiOk] = useState<boolean | null>(null)
  const [dbOk, setDbOk] = useState<boolean | null>(null)
  const [diagErr, setDiagErr] = useState<string | null>(null)
  const [welcome, setWelcome] = useState<{ text: string } | null>(null)
  useEffect(() => {
    let mounted = true
    api.get('/health/info')
      .then((res) => {
        if (!mounted) return
        const data = res.data || {}
        const v = data?.version as string | undefined
        if (v) setVersion(v)
        setBranch((data?.branch as string | undefined) || null)
        setCommit((data?.commit as string | undefined) || null)
        setBuildTime((data?.build_time as string | undefined) || null)
      })
      .catch(() => {
        // silencioso, não crítico
      })
    // Deep diagnostics (API + DB)
    api.get('/health/deep')
      .then((res)=>{
        if (!mounted) return
        const d = res.data || {}
        setApiOk(Boolean(d?.ok))
        setDbOk(Boolean(d?.db?.ok))
        setDiagErr(null)
      })
      .catch((e:any)=>{
        if (!mounted) return
        setApiOk(null)
        setDbOk(null)
        setDiagErr(e?.message||'Network Error')
      })
    return () => { mounted = false }
  }, [])
  // When tenant changes, show welcome popup and trigger lightweight refresh hints
  useEffect(()=>{
    const handler = (ev: any) => {
      try {
        const id = ev?.detail?.tenantId as string | undefined
        const tn = (tenants||[]).find(x => (x.id as any) === id)
        const name = (tn?.name as string) || id || ''
        const welcomeText = t('welcome_to_lab', { name }) as string
        const fallbackWelcome = name ? `${t('Bem-vindo')} — ${name}` : t('Bem-vindo')
        const text = welcomeText || fallbackWelcome
        setWelcome({ text })
        // auto-hide after a short delay
        setTimeout(()=> setWelcome(null), 2500)
      } catch {}
      // Hint: trigger a lightweight refresh signal other parts can listen to
      try { globalThis.dispatchEvent(new CustomEvent('tenant:refresh', { detail: ev?.detail })) } catch {}
      // optional: ping something lightweight to keep status updated
      api.get('/health').catch(()=>{})
    }
    globalThis.addEventListener('tenant:changed', handler)
    return () => globalThis.removeEventListener('tenant:changed', handler)
  }, [t, tenants])
  const shortCommit = commit ? commit.substring(0, 7) : null
  let versionTooltip: string | undefined
  if (version) {
    const lines: string[] = []
    lines.push(`Branch: ${branch || 'unknown'}`)
    lines.push(`Commit: ${shortCommit || 'unknown'}`)
    if (buildTime) {
      lines.push(`Build: ${buildTime}`)
    }
    versionTooltip = lines.join('\n')
  }
  // Status dot for quick glance (green: ok, yellow: db warn, red: error)
  let statusColor = 'bg-gray-400'
  let statusTip = 'Unknown'
  if (diagErr) { statusColor = 'bg-red-500'; statusTip = `API error: ${diagErr}` }
  else if (apiOk === true && dbOk === false) { statusColor = 'bg-yellow-500'; statusTip = 'API OK, DB unreachable' }
  else if (apiOk === true && dbOk === true) { statusColor = 'bg-green-600'; statusTip = 'API OK, DB OK' }
  return (
    <header className="w-full border-b bg-white/70 dark:bg-gray-900/70 backdrop-blur sticky top-0 z-10">
      <div className="h-14 px-4 flex items-center justify-between topbar-container">
        <div className="flex items-center gap-3 topbar-left">
          {/* Logo + Dashboard Link */}
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity mr-2">
            <img src="/assets/logos/vivae-erp-logo-main.svg" alt="VIVAE ERP" className="h-7 w-auto" />
            <span className="font-bold text-lg">VIVAE ERP</span>
          </Link>
          
          <span className="text-gray-300 dark:text-gray-600">|</span>
          
          {/* Breadcrumbs - caminho completo clicável */}
          <Breadcrumbs />
          
          <span title={statusTip} className={`inline-block w-2.5 h-2.5 rounded-full ${statusColor}`} />
          {version && (
            <span
              title={versionTooltip}
              className="text-xs rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 px-2 py-0.5"
            >
              {version}
            </span>
          )}
          <GlobalSearch />
          <select className="px-2 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-800" value={tenantId || ''} onChange={(e)=>setTenant(e.target.value)}>
            {(tenants||[]).map(tn => (<option key={tn.id} value={tn.id}>{tn.name}</option>))}
          </select>
          <DiagnosticsButton />
        </div>
        <div className="flex items-center gap-2 topbar-right">
          {/* Saudação no canto superior direito */}
          <span className="text-sm font-medium text-gray-700 dark:text-gray-200 mr-2">
            {t('Bem-vindo')}, {user?.username || 'user'} ({lang})
          </span>
          <LanguageSwitcher />
          <ThemeToggle />
          <button onClick={logout} className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('logout')}</button>
        </div>
      </div>
      {/* Welcome toast under the topbar */}
      {welcome && (
        <div className="fixed left-1/2 -translate-x-1/2 top-16 z-20">
          <div className="px-4 py-2 rounded-md shadow-lg bg-white/95 dark:bg-gray-800/95 border border-gray-200 dark:border-gray-700 text-sm">
            {welcome.text}
          </div>
        </div>
      )}
    </header>
  )
}

function DiagnosticsButton(){
  const [open, setOpen] = useState(false)
  return (
    <>
      <button onClick={()=>setOpen(true)} className="px-2 py-1 rounded border text-xs">Diag</button>
      {open && <DiagnosticsPanel onClose={()=>setOpen(false)} />}
    </>
  )
}

function DiagnosticsPanel({ onClose }:{ onClose:()=>void }){
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [base, setBase] = useState<string>(api.defaults.baseURL || '')
  const [ping, setPing] = useState<any>(null)
  const [info, setInfo] = useState<any>(null)
  const [deep, setDeep] = useState<any>(null)
  const [error, setError] = useState<string>('')
  const run = async ()=>{
    setLoading(true); setError('')
    try {
      const [p, i, d] = await Promise.allSettled([
        api.get('/health'),
        api.get('/health/info'),
        api.get('/health/deep'),
      ])
      setPing(p.status==='fulfilled'? p.value.data: { error: (p as any).reason?.message || 'err' })
      setInfo(i.status==='fulfilled'? i.value.data: { error: (i as any).reason?.message || 'err' })
      setDeep(d.status==='fulfilled'? d.value.data: { error: (d as any).reason?.message || 'err' })
    } catch(e:any){ setError(e?.message||'error') } finally { setLoading(false) }
  }
  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-900 rounded-md shadow-xl w-full max-w-2xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">Diagnostics</h3>
          <button onClick={onClose}>✕</button>
        </div>
        <div className="space-y-2 text-sm">
          <div><b>API Base:</b> {base}</div>
          <div className="flex gap-2">
            <button onClick={run} className="px-2 py-1 rounded border" disabled={loading}>{loading? '…': 'Run'}</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="border rounded p-2">
              <div className="font-medium">/api/health</div>
              <pre className="text-xs whitespace-pre-wrap break-words">{JSON.stringify(ping,null,2)}</pre>
            </div>
            <div className="border rounded p-2">
              <div className="font-medium">/api/health/info</div>
              <pre className="text-xs whitespace-pre-wrap break-words">{JSON.stringify(info,null,2)}</pre>
            </div>
            <div className="border rounded p-2">
              <div className="font-medium">/api/health/deep</div>
              <pre className="text-xs whitespace-pre-wrap break-words">{JSON.stringify(deep,null,2)}</pre>
            </div>
          </div>
          {error && (<div className="text-red-600">{error}</div>)}
          <div className="text-xs text-gray-500">
            Dicas: se /api/health falhar, verifique VITE_API_BASE no frontend. Se deep.db.ok for false, pode ser Atlas.
          </div>
        </div>
      </div>
    </div>
  )
}

