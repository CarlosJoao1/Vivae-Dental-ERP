import React from 'react'
import {
  listClients, createClient, updateClient, deleteClient,
  listPatients, createPatient, updatePatient, deletePatient,
  listTechnicians, createTechnician, updateTechnician, deleteTechnician,
  listServices, createService, updateService, deleteService,
  listDocumentTypes, createDocumentType, updateDocumentType, deleteDocumentType,
  Client, Patient, Laboratory, listLaboratories, updateLaboratory,
  listCurrencies, createCurrency, listPaymentTypes, createPaymentType, listPaymentForms, createPaymentForm, listPaymentMethods, createPaymentMethod,
  listSeries, createSeries, updateSeries, getSmtpConfig, updateSmtpConfig, testSmtp, diagnoseSmtp, type SmtpConfig,
  listCountries, createCountry, updateCountry, deleteCountry, type Country,
  listShippingAddresses, createShippingAddress, updateShippingAddress, deleteShippingAddress, type ShippingAddress
} from '@/api/masterdata'
import { useTranslation } from 'react-i18next'
import ClientsManager from '@/pages/ClientsManager'

function useList<T>(fetcher: (q?: string) => Promise<{ total: number, items: T[] }>) {
  const [q, setQ] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const [items, setItems] = React.useState<T[]>([])

  // Stabilize fetcher to avoid re-renders causing infinite loops
  const fetcherRef = React.useRef(fetcher)
  React.useEffect(() => { fetcherRef.current = fetcher }, [fetcher])

  const load = React.useCallback(async () => {
    setLoading(true)
    try {
      const { items } = await fetcherRef.current(q)
      setItems(items)
    } finally {
      setLoading(false)
    }
  }, [q])

  React.useEffect(()=>{ load() }, [load])
  return { q, setQ, loading, items, reload: load }
}

function SectionHeader({ title, onReload }: { title: string, onReload: ()=>void }){
  const { t } = useTranslation()
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      <button onClick={onReload} className="px-3 py-1 rounded border">{t('reload')}</button>
    </div>
  )
}

function Modal({ open, title, children, onClose }: { open: boolean; title: string; children: React.ReactNode; onClose: ()=>void }){
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="px-2 py-1">✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

function Clients(){
  const { t } = useTranslation()
  const { q, setQ, loading, items, reload } = useList((q) => listClients(q))
  const [form, setForm] = React.useState<{ code?: string; name?: string; first_name: string; last_name: string; gender: 'male'|'female'|'other'; birthdate: string; address: string; postal_code?: string; country_code?: string; type: 'clinic'|'dentist'|'other'; tax_id: string; email: string; phone: string; default_shipping_address?: string; location_code?: string; preferred_currency?: string; payment_type?: string; payment_form?: string; payment_method?: string }>(
    { code:'', name:'', first_name:'', last_name:'', gender:'other', birthdate:'', address:'', postal_code:'', country_code:'', type:'clinic', tax_id:'', email:'', phone:'', default_shipping_address:'', location_code:'', preferred_currency:'', payment_type:'', payment_form:'', payment_method:'' }
  )
  const [err, setErr] = React.useState<string>('')
  // Countries & shipping addresses for selects
  const [countries, setCountries] = React.useState<any[]>([])
  const [shipAddrs, setShipAddrs] = React.useState<any[]>([])
  React.useEffect(()=>{ (async()=>{ try{ const cs = await listCountries(); setCountries(cs.items||[]) }catch{} try{ const sa = await listShippingAddresses(); setShipAddrs(sa.items||[]) }catch{} })() }, [])
  // Financial lists for selects
  const [currs, setCurrs] = React.useState<any[]>([])
  const [payTypes, setPayTypes] = React.useState<any[]>([])
  const [payForms, setPayForms] = React.useState<any[]>([])
  const [payMethods, setPayMethods] = React.useState<any[]>([])
  React.useEffect(()=>{ (async ()=>{
    try {
      const r1 = await listCurrencies(); setCurrs(r1.items||[])
      const r2 = await listPaymentTypes(); setPayTypes(r2.items||[])
      const r3 = await listPaymentForms(); setPayForms(r3.items||[])
      const r4 = await listPaymentMethods(); setPayMethods(r4.items||[])
    } catch {}
  })() }, [])
  const submit = async (e: React.FormEvent)=>{
    e.preventDefault();
    setErr('')
    try {
      const name = `${form.first_name} ${form.last_name}`.trim() || form.name || ''
      const body: Partial<Client> = { ...form, name, country_code: (form.country_code||'').toUpperCase() || undefined }
      await createClient(body)
      setForm({ code:'', name:'', first_name:'', last_name:'', gender:'other', birthdate:'', address:'', postal_code:'', country_code:'', type:'clinic', tax_id:'', email:'', phone:'', default_shipping_address:'', location_code:'', preferred_currency:'', payment_type:'', payment_form:'', payment_method:''});
      reload()
    } catch (e: any) {
      setErr(e?.response?.data?.error || e?.message || 'Error')
    }
  }
  const remove = async (id: string)=>{ await deleteClient(id); reload() }

  // Edit modal
  const [editing, setEditing] = React.useState<Client | null>(null)
  const [editForm, setEditForm] = React.useState<Partial<Client>>({})
  const [editErr, setEditErr] = React.useState<string>('')
  const openEdit = (c: Client) => { setEditing(c); setEditForm({ ...c }) }
  const closeEdit = () => { setEditing(null); setEditForm({}) }
  const saveEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editing?.id) return
    setEditErr('')
    try {
      const body: Partial<Client> = { ...editForm, country_code: ((editForm as any).country_code||'').toUpperCase() || undefined }
      await updateClient(editing.id, body)
      closeEdit(); reload()
    } catch (e: any) {
      setEditErr(e?.response?.data?.error || e?.message || 'Error')
    }
  }

  return (
    <div>
      <SectionHeader title={t('clients')} onReload={reload} />
      <div className="flex items-center gap-2 mb-2">
        <input placeholder={t('search') as string} value={q} onChange={e=>setQ(e.target.value)} className="input" />
        {loading && <span>…</span>}
      </div>
      {err && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{err}</div>}
      <form onSubmit={submit} className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        <input placeholder={t('first_name') as string} value={form.first_name} onChange={e=>setForm({...form, first_name: e.target.value})} className="input" />
        <input placeholder={t('last_name') as string} value={form.last_name} onChange={e=>setForm({...form, last_name: e.target.value})} className="input" />
        <input placeholder={t('name') as string || 'Name'} value={form.name||''} onChange={e=>setForm({...form, name: e.target.value})} className="input col-span-2" />
        <select value={form.gender} onChange={e=>setForm({...form, gender: e.target.value as 'male'|'female'|'other'})} className="input">
          <option value="male">{t('male')}</option>
          <option value="female">{t('female')}</option>
          <option value="other">{t('other')}</option>
        </select>
        <input type="date" placeholder={t('birthdate') as string} value={form.birthdate} onChange={e=>setForm({...form, birthdate: e.target.value})} className="input" />
        <input placeholder={t('address') as string} value={form.address} onChange={e=>setForm({...form, address: e.target.value})} className="input col-span-2" />
        <input placeholder={t('postal_code') as string || 'Código Postal'} value={form.postal_code||''} onChange={e=>setForm({...form, postal_code: e.target.value})} className="input" />
        <select value={form.country_code||''} onChange={e=>setForm({...form, country_code: e.target.value})} className="input">
          <option value="">{t('country') as string || 'País'}</option>
          {countries.map((c:any)=> (<option key={c.id} value={c.code}>{c.code} - {c.name}</option>))}
        </select>
        <input placeholder={t('email') as string} value={form.email} onChange={e=>setForm({...form, email: e.target.value})} className="input" />
        <input placeholder={t('phone') as string} value={form.phone} onChange={e=>setForm({...form, phone: e.target.value})} className="input" />
        <select value={form.type} onChange={e=>setForm({...form, type: e.target.value as 'clinic'|'dentist'|'other'})} className="input">
          <option value="clinic">Clinic</option>
          <option value="dentist">Dentist</option>
          <option value="other">Other</option>
        </select>
        <input placeholder={t('tax_id') as string} value={form.tax_id} onChange={e=>setForm({...form, tax_id: e.target.value})} className="input" />
        <select value={form.default_shipping_address||''} onChange={e=>setForm({...form, default_shipping_address: e.target.value})} className="input">
          <option value="">{t('default_shipping_address') as string || 'Endereço Envio (predef.)'}</option>
          {shipAddrs.map((a:any)=> (<option key={a.id} value={a.code}>{a.code} - {a.address1}</option>))}
        </select>
        <input placeholder={t('location_code') as string || 'Código Localização'} value={form.location_code||''} onChange={e=>setForm({...form, location_code: e.target.value})} className="input" />
        <select value={form.preferred_currency||''} onChange={e=>setForm({...form, preferred_currency: e.target.value})} className="input">
          <option value="">{t('currencies')}</option>
          {currs.map(c=> (<option key={c.id} value={c.id}>{c.code} {c.name? `- ${c.name}`:''}</option>))}
        </select>
        <select value={form.payment_type||''} onChange={e=>setForm({...form, payment_type: e.target.value})} className="input">
          <option value="">{t('payment_types')}</option>
          {payTypes.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
        </select>
        <select value={form.payment_form||''} onChange={e=>setForm({...form, payment_form: e.target.value})} className="input">
          <option value="">{t('payment_forms')}</option>
          {payForms.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
        </select>
        <select value={form.payment_method||''} onChange={e=>setForm({...form, payment_method: e.target.value})} className="input">
          <option value="">{t('payment_methods')}</option>
          {payMethods.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
        </select>
        <button className="btn btn-primary col-span-2 md:col-span-1">{t('create')}</button>
      </form>
      <table className="w-full text-sm">
        <thead><tr>
          <th className="text-left">{t('name')}</th>
          <th>{t('birthdate')}</th>
          <th>{t('age')}</th>
          <th>{t('email')}</th>
          <th>{t('phone')}</th>
          <th>{t('tax_id')}</th>
          <th></th>
        </tr></thead>
        <tbody>
          {items.map((c:any)=> (
            <tr key={c.id} className="border-t">
              <td className="py-1">{c.first_name || c.last_name ? `${c.first_name||''} ${c.last_name||''}`.trim() : (c.name || '')}</td>
              <td className="text-center">{c.birthdate ? new Date(c.birthdate).toLocaleDateString() : ''}</td>
              <td className="text-center">{c.age ?? ''}</td>
              <td className="text-center">{c.email || ''}</td>
              <td className="text-center">{c.phone || ''}</td>
              <td className="text-center">{c.tax_id || ''}</td>
              <td className="text-right flex gap-2 justify-end">
                <button onClick={()=>openEdit(c)} className="text-blue-600">{t('edit')}</button>
                <button onClick={()=>remove(c.id)} className="text-red-600">{t('remove')}</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Modal open={!!editing} title={t('edit') as string} onClose={closeEdit}>
        {editErr && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{editErr}</div>}
        <form onSubmit={saveEdit} className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <input placeholder={(t('code') as string)||'Code'} value={(editForm as any).code || ''} onChange={e=>setEditForm({...editForm, code: e.target.value})} className="input" />
          <input placeholder={t('first_name') as string} value={editForm.first_name || ''} onChange={e=>setEditForm({...editForm, first_name: e.target.value})} className="input" />
          <input placeholder={t('last_name') as string} value={editForm.last_name || ''} onChange={e=>setEditForm({...editForm, last_name: e.target.value})} className="input" />
          <input placeholder={t('name') as string || 'Name'} value={(editForm as any).name || ''} onChange={e=>setEditForm({...editForm, name: e.target.value})} className="input col-span-2" />
          <select value={editForm.gender || 'other'} onChange={e=>setEditForm({...editForm, gender: e.target.value as 'male'|'female'|'other'})} className="input">
            <option value="male">{t('male')}</option>
            <option value="female">{t('female')}</option>
            <option value="other">{t('other')}</option>
          </select>
          <input type="date" value={(editForm.birthdate as string) || ''} onChange={e=>setEditForm({...editForm, birthdate: e.target.value})} className="input" />
          <input placeholder={t('address') as string} value={editForm.address || ''} onChange={e=>setEditForm({...editForm, address: e.target.value})} className="input col-span-2" />
          <input placeholder={t('postal_code') as string || 'Código Postal'} value={(editForm as any).postal_code || ''} onChange={e=>setEditForm({...editForm, postal_code: e.target.value})} className="input" />
          <select value={(editForm as any).country_code || ''} onChange={e=>setEditForm({...editForm, country_code: e.target.value})} className="input">
            <option value="">{t('country') as string || 'País'}</option>
            {countries.map((c:any)=> (<option key={c.id} value={c.code}>{c.code} - {c.name}</option>))}
          </select>
          <input placeholder={t('email') as string} value={editForm.email || ''} onChange={e=>setEditForm({...editForm, email: e.target.value})} className="input" />
          <input placeholder={t('phone') as string} value={editForm.phone || ''} onChange={e=>setEditForm({...editForm, phone: e.target.value})} className="input" />
          <input placeholder={t('tax_id') as string} value={editForm.tax_id || ''} onChange={e=>setEditForm({...editForm, tax_id: e.target.value})} className="input" />
          <select value={(editForm as any).default_shipping_address || ''} onChange={e=>setEditForm({...editForm, default_shipping_address: e.target.value})} className="input">
            <option value="">{t('default_shipping_address') as string || 'Endereço Envio (predef.)'}</option>
            {shipAddrs.map((a:any)=> (<option key={a.id} value={a.code}>{a.code} - {a.address1}</option>))}
          </select>
          <input placeholder={t('location_code') as string || 'Código Localização'} value={(editForm as any).location_code || ''} onChange={e=>setEditForm({...editForm, location_code: e.target.value})} className="input" />
          <select value={(editForm as any).preferred_currency || ''} onChange={e=>setEditForm({...editForm, preferred_currency: e.target.value})} className="input">
            <option value="">{t('currencies')}</option>
            {currs.map(c=> (<option key={c.id} value={c.id}>{c.code} {c.name? `- ${c.name}`:''}</option>))}
          </select>
          <select value={(editForm as any).payment_type || ''} onChange={e=>setEditForm({...editForm, payment_type: e.target.value})} className="input">
            <option value="">{t('payment_types')}</option>
            {payTypes.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <select value={(editForm as any).payment_form || ''} onChange={e=>setEditForm({...editForm, payment_form: e.target.value})} className="input">
            <option value="">{t('payment_forms')}</option>
            {payForms.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <select value={(editForm as any).payment_method || ''} onChange={e=>setEditForm({...editForm, payment_method: e.target.value})} className="input">
            <option value="">{t('payment_methods')}</option>
            {payMethods.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <div className="col-span-2 md:col-span-4 flex justify-end gap-2">
            <button type="button" onClick={closeEdit} className="px-3 py-1 rounded border">{t('cancel')}</button>
            <button type="submit" className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('save')}</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

function Patients(){
  const { t } = useTranslation()
  const { q, setQ, loading, items, reload } = useList((q) => listPatients(q))
  const [form, setForm] = React.useState<{ first_name: string; last_name: string; gender: 'male'|'female'|'other'; birthdate: string; address: string; email: string; phone: string }>(
    { first_name:'', last_name:'', gender:'other', birthdate:'', address:'', email:'', phone:'' }
  )
  const submit = async (e: React.FormEvent)=>{
    e.preventDefault();
    const name = `${form.first_name} ${form.last_name}`.trim()
    const body: Partial<Patient> = { ...form, name }
    await createPatient(body); setForm({ first_name:'', last_name:'', gender:'other', birthdate:'', address:'', email:'', phone:''}); reload()
  }
  const remove = async (id: string)=>{ await deletePatient(id); reload() }
  return (
    <div>
      <SectionHeader title={t('patients')} onReload={reload} />
      <div className="flex items-center gap-2 mb-2">
        <input placeholder={t('search') as string} value={q} onChange={e=>setQ(e.target.value)} className="input" />
        {loading && <span>…</span>}
      </div>
      <form onSubmit={submit} className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        <input placeholder={t('first_name') as string} value={form.first_name} onChange={e=>setForm({...form, first_name: e.target.value})} className="input" />
        <input placeholder={t('last_name') as string} value={form.last_name} onChange={e=>setForm({...form, last_name: e.target.value})} className="input" />
        <select value={form.gender} onChange={e=>setForm({...form, gender: e.target.value as 'male'|'female'|'other'})} className="input">
          <option value="male">{t('male')}</option>
          <option value="female">{t('female')}</option>
          <option value="other">{t('other')}</option>
        </select>
        <input type="date" placeholder={t('birthdate') as string} value={form.birthdate} onChange={e=>setForm({...form, birthdate: e.target.value})} className="input" />
        <input placeholder={t('address') as string} value={form.address} onChange={e=>setForm({...form, address: e.target.value})} className="input col-span-2" />
        <input placeholder={t('email') as string} value={form.email} onChange={e=>setForm({...form, email: e.target.value})} className="input" />
        <input placeholder={t('phone') as string} value={form.phone} onChange={e=>setForm({...form, phone: e.target.value})} className="input" />
        <button className="btn btn-primary col-span-2 md:col-span-1">{t('create')}</button>
      </form>
      <ul className="space-y-1">
        {items.map((p:any)=> (
          <li key={p.id} className="border p-2 rounded">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{p.first_name || p.last_name ? `${p.first_name||''} ${p.last_name||''}`.trim() : (p.name || '')}</div>
                <div className="text-xs text-gray-500">{[p.birthdate ? new Date(p.birthdate).toLocaleDateString() : '', p.age != null ? `${p.age} ${t('age')}` : ''].filter(Boolean).join(' · ')}</div>
              </div>
              <button onClick={()=>remove(p.id)} className="text-red-600">{t('remove')}</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Technicians(){
  const { t } = useTranslation()
  const { q, setQ, loading, items, reload } = useList((q) => listTechnicians(q))
  const [form, setForm] = React.useState({ name: '' })
  const submit = async (e: React.FormEvent)=>{ e.preventDefault(); await createTechnician(form); setForm({ name:''}); reload() }
  const remove = async (id: string)=>{ await deleteTechnician(id); reload() }
  return (
    <div>
      <SectionHeader title={t('technicians')} onReload={reload} />
      <div className="flex items-center gap-2 mb-2">
        <input placeholder={t('search') as string} value={q} onChange={e=>setQ(e.target.value)} className="input" />
        {loading && <span>…</span>}
      </div>
      <form onSubmit={submit} className="flex gap-2 mb-3">
        <input placeholder={t('name') as string} value={form.name} onChange={e=>setForm({...form, name: e.target.value})} className="input" />
        <button className="btn btn-primary">{t('create')}</button>
      </form>
      <ul className="space-y-1">
        {items.map((tech:any)=> (
          <li key={tech.id} className="border p-2 rounded flex items-center justify-between">
            <div>{tech.name}</div>
            <button onClick={()=>remove(tech.id)} className="text-red-600">{t('remove')}</button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Services(){
  const { t } = useTranslation()
  const { q, setQ, loading, items, reload } = useList((q) => listServices(q))
  const [form, setForm] = React.useState({ name: '', code: '', price: 0 })
  const submit = async (e: React.FormEvent)=>{ e.preventDefault(); await createService({ ...form, price: Number(form.price) || 0 }); setForm({ name:'', code:'', price:0}); reload() }
  const remove = async (id: string)=>{ await deleteService(id); reload() }
  return (
    <div>
      <SectionHeader title={t('services')} onReload={reload} />
      <div className="flex items-center gap-2 mb-2">
        <input placeholder={t('search') as string} value={q} onChange={e=>setQ(e.target.value)} className="input" />
        {loading && <span>…</span>}
      </div>
      <form onSubmit={submit} className="flex gap-2 mb-3">
        <input placeholder={t('name') as string} value={form.name} onChange={e=>setForm({...form, name: e.target.value})} className="input" />
        <input placeholder={t('code') as string} value={form.code} onChange={e=>setForm({...form, code: e.target.value})} className="input" />
        <input type="number" step="0.01" placeholder={t('price') as string} value={form.price} onChange={e=>setForm({...form, price: Number(e.target.value)})} className="input" />
        <button className="btn btn-primary">{t('create')}</button>
      </form>
      <table className="w-full text-sm">
        <thead><tr><th className="text-left">{t('name')}</th><th>{t('code')}</th><th>{t('price')}</th><th></th></tr></thead>
        <tbody>
          {items.map((s:any)=> (
            <tr key={s.id} className="border-t">
              <td className="py-1">{s.name}</td>
              <td className="text-center">{s.code || ''}</td>
              <td className="text-center">{s.price ?? ''}</td>
              <td className="text-right"><button onClick={()=>remove(s.id)} className="text-red-600">{t('remove')}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function DocumentTypes(){
  const { t } = useTranslation()
  const { q, setQ, loading, items, reload } = useList((q) => listDocumentTypes(q))
  const [form, setForm] = React.useState({ name: '', extension: '' })
  const submit = async (e: React.FormEvent)=>{ e.preventDefault(); await createDocumentType(form); setForm({ name:'', extension:''}); reload() }
  const remove = async (id: string)=>{ await deleteDocumentType(id); reload() }
  return (
    <div>
      <SectionHeader title={t('document_types')} onReload={reload} />
      <div className="flex items-center gap-2 mb-2">
        <input placeholder={t('search') as string} value={q} onChange={e=>setQ(e.target.value)} className="input" />
        {loading && <span>…</span>}
      </div>
      <form onSubmit={submit} className="flex gap-2 mb-3">
        <input placeholder={t('name') as string} value={form.name} onChange={e=>setForm({...form, name: e.target.value})} className="input" />
        <input placeholder={t('extension') as string} value={form.extension} onChange={e=>setForm({...form, extension: e.target.value})} className="input" />
        <button className="btn btn-primary">{t('create')}</button>
      </form>
      <ul className="space-y-1">
        {items.map((d:any)=> (
          <li key={d.id} className="border p-2 rounded flex items-center justify-between">
            <div>{d.name} {d.extension? `(.${d.extension})`:''}</div>
            <button onClick={()=>remove(d.id)} className="text-red-600">{t('remove')}</button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Currencies(){
  const { t } = useTranslation()
  const [items, setItems] = React.useState<any[]>([])
  const [form, setForm] = React.useState({ code: '', name: '', symbol: '', is_default: false })
  const reload = async ()=>{ const { items } = await listCurrencies(); setItems(items) }
  React.useEffect(()=>{ reload() }, [])
  const submit = async (e: React.FormEvent)=>{ e.preventDefault(); await createCurrency(form); setForm({ code:'', name:'', symbol:'', is_default:false}); reload() }
  return (
    <div>
      <SectionHeader title={t('currencies')} onReload={reload} />
      <form onSubmit={submit} className="flex flex-wrap gap-2 mb-3">
        <input placeholder={t('code') as string} value={form.code} onChange={e=>setForm({...form, code:e.target.value})} className="input" />
        <input placeholder={t('name') as string} value={form.name} onChange={e=>setForm({...form, name:e.target.value})} className="input" />
        <input placeholder={t('symbol') as string} value={form.symbol} onChange={e=>setForm({...form, symbol:e.target.value})} className="input" />
        <label className="flex items-center gap-2"><input type="checkbox" checked={form.is_default} onChange={e=>setForm({...form, is_default:e.target.checked})} />{t('is_default')}</label>
        <button className="btn btn-primary">{t('create')}</button>
      </form>
      <table className="w-full text-sm"><thead><tr><th>{t('code')}</th><th>{t('name')}</th><th>{t('symbol')}</th><th>{t('is_default')}</th></tr></thead><tbody>
        {items.map((c:any)=>(<tr key={c.id} className="border-t"><td className="text-center">{c.code}</td><td className="text-center">{c.name}</td><td className="text-center">{c.symbol}</td><td className="text-center">{c.is_default? '✓':''}</td></tr>))}
      </tbody></table>
    </div>
  )
}

function SimpleFinList({ title, loader, creator }:{ title:string, loader:()=>Promise<{items:any[]}>, creator:(body:any)=>Promise<any> }){
  const { t } = useTranslation()
  const [items, setItems] = React.useState<any[]>([])
  const [form, setForm] = React.useState<{ code?: string; name: string }>({ code:'', name:'' })
  const reload = async ()=>{ const { items } = await loader(); setItems(items) }
  React.useEffect(()=>{ reload() }, [])
  const submit = async (e: React.FormEvent)=>{ e.preventDefault(); await creator(form); setForm({ code:'', name:''}); reload() }
  return (
    <div>
      <SectionHeader title={title} onReload={reload} />
      <form onSubmit={submit} className="flex flex-wrap gap-2 mb-3">
        <input placeholder={t('code') as string} value={form.code} onChange={e=>setForm({...form, code:e.target.value})} className="input" />
        <input placeholder={t('name') as string} value={form.name} onChange={e=>setForm({...form, name:e.target.value})} className="input" />
        <button className="btn btn-primary">{t('create')}</button>
      </form>
      <table className="w-full text-sm"><thead><tr><th>{t('code')}</th><th>{t('name')}</th></tr></thead><tbody>
        {items.map((it:any)=>(<tr key={it.id} className="border-t"><td className="text-center">{it.code||''}</td><td className="text-center">{it.name}</td></tr>))}
      </tbody></table>
    </div>
  )
}

export default function MasterData(){
  const { t } = useTranslation()
  const tabs: Array<{key: 'clients'|'clients_list'|'patients'|'technicians'|'services'|'doctypes'|'currencies'|'payment_types'|'payment_forms'|'payment_methods'|'series'|'smtp'|'lab'|'countries'|'shipping_addresses', label: string}> = [
    { key: 'lab', label: (t('laboratory') as string) || 'Laboratory' },
    { key: 'clients', label: t('clients') as string },
    { key: 'clients_list', label: (t('all_clients') as string) || 'Todos os Clientes' },
    { key: 'patients', label: t('patients') as string },
    { key: 'technicians', label: t('technicians') as string },
    { key: 'services', label: t('services') as string },
    { key: 'doctypes', label: t('document_types') as string },
    { key: 'countries', label: (t('countries') as string) || 'Countries' },
    { key: 'shipping_addresses', label: (t('shipping_addresses') as string) || 'Shipping Addresses' },
    { key: 'currencies', label: t('currencies') as string },
    { key: 'payment_types', label: t('payment_types') as string },
    { key: 'payment_forms', label: t('payment_forms') as string },
    { key: 'payment_methods', label: t('payment_methods') as string },
    { key: 'series', label: (t('series') as string) || 'Series' },
    { key: 'smtp', label: (t('smtp_settings') as string) || 'SMTP' },
  ]
  const [tab, setTab] = React.useState<'lab'|'clients'|'clients_list'|'patients'|'technicians'|'services'|'doctypes'|'countries'|'shipping_addresses'|'currencies'|'payment_types'|'payment_forms'|'payment_methods'|'series'|'smtp'>('clients')
  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">{t('masterdata')}</h1>
      <div className="flex gap-2 mb-4">
        {tabs.map(ti => (
          <button key={ti.key} onClick={()=>setTab(ti.key)} className={`px-3 py-1 rounded border ${tab===ti.key?'bg-gray-900 text-white dark:bg-gray-700':''}`}>{ti.label}</button>
        ))}
      </div>
      <div className="space-y-6">
  {tab==='lab' && <LabSettings/>}
  {tab==='clients' && <Clients/>}
        {tab==='patients' && <Patients/>}
  {tab==='clients_list' && <ClientsManager />}
        {tab==='technicians' && <Technicians/>}
        {tab==='services' && <Services/>}
        {tab==='doctypes' && <DocumentTypes/>}
        {tab==='countries' && <CountriesTab />}
        {tab==='shipping_addresses' && <ShippingAddressesTab />}
        {tab==='currencies' && <Currencies/>}
        {tab==='payment_types' && <SimpleFinList title={t('payment_types') as string} loader={listPaymentTypes} creator={createPaymentType} />}
        {tab==='payment_forms' && <SimpleFinList title={t('payment_forms') as string} loader={listPaymentForms} creator={createPaymentForm} />}
        {tab==='payment_methods' && <SimpleFinList title={t('payment_methods') as string} loader={listPaymentMethods} creator={createPaymentMethod} />}
        {tab==='series' && <SeriesTab />}
        {tab==='smtp' && <SmtpTab />}
      </div>
    </div>
  )
}

function CountriesTab(){
  const { t } = useTranslation()
  const [items, setItems] = React.useState<Country[]>([])
  const [form, setForm] = React.useState<Partial<Country>>({ code: '', name: '' })
  const [editingId, setEditingId] = React.useState<string>('')
  const [err, setErr] = React.useState<string>('')
  const reload = async ()=>{ const { items } = await listCountries(); setItems(items||[]) }
  React.useEffect(()=>{ reload() }, [])
  const submit = async (e: React.FormEvent)=>{
    e.preventDefault();
    setErr('')
    if (!form.code || !form.name) return;
    try {
      if (editingId) {
        await updateCountry(editingId, { code: String(form.code).toUpperCase(), name: form.name })
        setEditingId('')
      } else {
        await createCountry({ code: String(form.code).toUpperCase(), name: form.name })
      }
      setForm({ code:'', name:'' }); reload()
    } catch (e:any) {
      const ref = e?.response?.data?.references
      const msg = e?.response?.data?.error || e?.message || 'Error'
      if (ref && (typeof ref.shipping_addresses !== 'undefined' || typeof ref.clients !== 'undefined')){
        setErr(`${msg}: SA=${ref.shipping_addresses||0}, Clients=${ref.clients||0}`)
      } else {
        setErr(String(msg))
      }
    }
  }
  const startEdit = (c: Country)=>{ setEditingId(c.id as string); setForm({ code: c.code, name: c.name }) }
  const remove = async (id: string)=>{
    setErr('')
    try { await deleteCountry(id); reload() } catch (e:any) {
      const ref = e?.response?.data?.references
      const msg = e?.response?.data?.error || e?.message || 'Error'
      if (ref && (typeof ref.shipping_addresses !== 'undefined' || typeof ref.clients !== 'undefined')){
        setErr(`${msg}: SA=${ref.shipping_addresses||0}, Clients=${ref.clients||0}`)
      } else { setErr(String(msg)) }
    }
  }
  return (
    <div>
      <SectionHeader title={(t('countries') as string) || 'Countries'} onReload={reload} />
      {err && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{err}</div>}
      <form onSubmit={submit} className="flex flex-wrap gap-2 mb-3">
        <input placeholder={(t('code') as string)||'Code'} value={form.code||''} onChange={e=>setForm({...form, code:e.target.value})} className="input" />
        <input placeholder={(t('name') as string)||'Name'} value={form.name||''} onChange={e=>setForm({...form, name:e.target.value})} className="input" />
        <button className="btn btn-primary">{editingId ? (t('save') as string) : (t('create') as string)}</button>
      </form>
      <table className="w-full text-sm"><thead><tr><th>{t('code')}</th><th>{t('name')}</th><th></th></tr></thead><tbody>
        {items.map(c=> (
          <tr key={c.id} className="border-t">
            <td className="text-center">{c.code}</td>
            <td className="text-center">{c.name}</td>
            <td className="text-right px-2 py-1 flex gap-2 justify-end">
              <button className="text-blue-600" onClick={()=>startEdit(c)}>{t('edit')}</button>
              <button className="text-red-600" onClick={()=>remove(c.id as string)}>{t('remove')}</button>
            </td>
          </tr>
        ))}
      </tbody></table>
    </div>
  )
}

function ShippingAddressesTab(){
  const { t } = useTranslation()
  const [items, setItems] = React.useState<ShippingAddress[]>([])
  const [countries, setCountries] = React.useState<Country[]>([])
  const [form, setForm] = React.useState<ShippingAddress>({ code:'', address1:'', address2:'', postal_code:'', city:'', country_code:'' })
  const [editingId, setEditingId] = React.useState<string>('')
  const [err, setErr] = React.useState<string>('')
  const reload = async ()=>{ const { items } = await listShippingAddresses(); setItems(items||[]) }
  React.useEffect(()=>{ reload(); (async()=>{ try{ const cs = await listCountries(); setCountries(cs.items||[]) }catch{} })() }, [])
  const submit = async (e: React.FormEvent)=>{
    e.preventDefault()
    setErr('')
    try{
      const body: Partial<ShippingAddress> = { ...form, country_code: (form.country_code||'').toUpperCase() }
      if (editingId) { await updateShippingAddress(editingId, body); setEditingId('') } else { await createShippingAddress(body) }
      setForm({ code:'', address1:'', address2:'', postal_code:'', city:'', country_code:'' }); reload()
    } catch(e:any){
      const msg = e?.response?.data?.error || e?.message || 'Error'
      setErr(String(msg))
    }
  }
  const startEdit = (it: ShippingAddress)=>{ setEditingId(it.id as string); setForm({ code: it.code, address1: it.address1, address2: it.address2, postal_code: it.postal_code, city: it.city, country_code: it.country_code }) }
  const remove = async (id: string)=>{ await deleteShippingAddress(id); reload() }
  return (
    <div>
      <SectionHeader title={(t('shipping_addresses') as string) || 'Shipping Addresses'} onReload={reload} />
      {err && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{err}</div>}
      <form onSubmit={submit} className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        <input placeholder={(t('code') as string)||'Code'} value={form.code||''} onChange={e=>setForm({...form, code:e.target.value})} className="input" />
        <input placeholder={(t('address1') as string)||'Address 1'} value={form.address1||''} onChange={e=>setForm({...form, address1:e.target.value})} className="input col-span-2" />
        <input placeholder={(t('address2') as string)||'Address 2'} value={form.address2||''} onChange={e=>setForm({...form, address2:e.target.value})} className="input col-span-2" />
        <input placeholder={(t('postal_code') as string)||'Postal Code'} value={form.postal_code||''} onChange={e=>setForm({...form, postal_code:e.target.value})} className="input" />
        <input placeholder={(t('city') as string)||'City'} value={form.city||''} onChange={e=>setForm({...form, city:e.target.value})} className="input" />
        <select value={form.country_code||''} onChange={e=>setForm({...form, country_code:e.target.value})} className="input">
          <option value="">{(t('country') as string)||'Country'}</option>
          {countries.map(c=> (<option key={c.id} value={c.code}>{c.code} - {c.name}</option>))}
        </select>
        <button className="btn btn-primary">{editingId ? (t('save') as string) : (t('create') as string)}</button>
      </form>
      <table className="w-full text-sm"><thead><tr>
        <th>{t('code')}</th><th>{t('address1')||'Address 1'}</th><th>{t('postal_code')||'Postal Code'}</th><th>{t('city')||'City'}</th><th>{t('country')||'Country'}</th><th></th>
      </tr></thead><tbody>
        {items.map((a:any)=> (
          <tr key={a.id} className="border-t">
            <td className="text-center">{a.code}</td>
            <td className="text-center">{a.address1}</td>
            <td className="text-center">{a.postal_code}</td>
            <td className="text-center">{a.city}</td>
            <td className="text-center">{a.country_code}</td>
            <td className="text-right px-2 py-1 flex gap-2 justify-end">
              <button className="text-blue-600" onClick={()=>startEdit(a)}>{t('edit')}</button>
              <button className="text-red-600" onClick={()=>remove(a.id)}>{t('remove')}</button>
            </td>
          </tr>
        ))}
      </tbody></table>
    </div>
  )
}

function LabSettings(){
  const { t } = useTranslation()
  const [labs, setLabs] = React.useState<Laboratory[]>([])
  const [form, setForm] = React.useState<Partial<Laboratory>>({})
  const [labId, setLabId] = React.useState<string>('')
  const reload = async ()=>{
    const { laboratories } = await listLaboratories()
    setLabs(laboratories||[])
    const first = laboratories?.[0]
    if (first) { setLabId(first.id as string); setForm(first) }
  }
  React.useEffect(()=>{ reload() }, [])
  const save = async (e: React.FormEvent)=>{ e.preventDefault(); if (!labId) return; const body = { ...form }; const saved = await updateLaboratory(labId, body); setForm(saved) }
  return (
    <div>
      <SectionHeader title={t('laboratory') as string || 'Laboratory'} onReload={reload} />
      {!labId && <div className="text-sm text-gray-500">{t('loading')||'Loading...'}</div>}
      {labId && (
        <form onSubmit={save} className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <input placeholder={t('name') as string || 'Name'} value={form.name||''} onChange={e=>setForm({...form, name:e.target.value})} className="input" />
          <input placeholder={t('address') as string || 'Address'} value={form.address||''} onChange={e=>setForm({...form, address:e.target.value})} className="input col-span-2" />
          <input placeholder={t('postal_code') as string || 'Postal Code'} value={form.postal_code||''} onChange={e=>setForm({...form, postal_code:e.target.value})} className="input" />
          <input placeholder={t('city') as string || 'City'} value={form.city||''} onChange={e=>setForm({...form, city:e.target.value})} className="input" />
          <input placeholder={t('country') as string || 'Country'} value={form.country||''} onChange={e=>setForm({...form, country:e.target.value})} className="input" />
          <input placeholder={t('tax_id') as string || 'Tax ID'} value={form.tax_id||''} onChange={e=>setForm({...form, tax_id:e.target.value})} className="input" />
          <input placeholder={t('phone') as string || 'Phone'} value={form.phone||''} onChange={e=>setForm({...form, phone:e.target.value})} className="input" />
          <input placeholder={t('email') as string || 'Email'} value={form.email||''} onChange={e=>setForm({...form, email:e.target.value})} className="input" />
          <input placeholder="Logo URL" value={form.logo_url||''} onChange={e=>setForm({...form, logo_url:e.target.value})} className="input col-span-2" />
          {form.logo_url ? <div className="col-span-2"><img src={form.logo_url} alt="logo" className="h-16 object-contain" /></div> : <div className="col-span-2 text-xs text-gray-500">{t('no_logo')||'No logo set'}</div>}
          <div className="col-span-2 md:col-span-4 flex justify-end">
            <button className="btn btn-primary">{t('save') as string || 'Save'}</button>
          </div>
        </form>
      )}
    </div>
  )
}

function SeriesTab(){
  const { t } = useTranslation()
  const [items, setItems] = React.useState<any[]>([])
  const [form, setForm] = React.useState<{ doc_type:'order'|'invoice'|'client'; prefix:string; next_number:number; padding:number; active:boolean }>({ doc_type:'order', prefix:'ORD-', next_number:1, padding:5, active:true })
  const [editingId, setEditingId] = React.useState<string>('')
  const reload = async ()=>{ const { items } = await listSeries(); setItems(items) }
  React.useEffect(()=>{ reload() }, [])
  const editing = React.useMemo(()=> items.find((s:any)=> s.id===editingId), [items, editingId])
  const docTypeLocked = !!editingId && ((editing?.next_number ?? 1) > 1)
  const submit = async (e: React.FormEvent)=>{ e.preventDefault(); if (editingId) { await updateSeries(editingId, form); setEditingId('') } else { await createSeries(form) } setForm({ doc_type:'order', prefix:'ORD-', next_number:1, padding:5, active:true }); reload() }
  return (
    <div>
      <SectionHeader title={(t('series') as string) || 'Series'} onReload={reload} />
      <form onSubmit={submit} className="flex flex-wrap gap-2 mb-3 items-center">
        <select value={form.doc_type} onChange={e=>setForm({...form, doc_type: e.target.value as any})} className="input" disabled={docTypeLocked}>
          <option value="order">{t('sales_orders')||'Orders'}</option>
          <option value="invoice">{t('sales_invoices')||'Invoices'}</option>
          <option value="client">{t('clients')||'Clients'}</option>
        </select>
        {docTypeLocked && <span className="text-xs text-amber-600">{t('doc_type_locked')||'Type locked (already used)'}</span>}
        <input placeholder={(t('prefix') as string) || 'Prefix'} value={form.prefix} onChange={e=>setForm({...form, prefix:e.target.value})} className="input" />
        <input type="number" placeholder={(t('next_number') as string) || 'Next'} value={form.next_number} onChange={e=>setForm({...form, next_number:Number(e.target.value)})} className="input" />
        <input type="number" placeholder={(t('padding') as string) || 'Padding'} value={form.padding} onChange={e=>setForm({...form, padding:Number(e.target.value)})} className="input" />
        <label className="flex items-center gap-2"><input type="checkbox" checked={form.active} onChange={e=>setForm({...form, active:e.target.checked})} />{(t('active') as string) || 'Active'}</label>
        <button className="btn btn-primary">{t('create')}</button>
      </form>
      <table className="w-full text-sm"><thead><tr><th>{(t('document_types') as string) || 'Type'}</th><th>{(t('prefix') as string) || 'Prefix'}</th><th>{(t('next_number') as string) || 'Next'}</th><th>{(t('padding') as string) || 'Padding'}</th><th>{(t('active') as string) || 'Active'}</th><th></th></tr></thead><tbody>
        {items.map((s:any)=> (
          <tr key={s.id} className="border-t">
            <td className="text-center">{s.doc_type}</td>
            <td className="text-center">{s.prefix}</td>
            <td className="text-center">{s.next_number}</td>
            <td className="text-center">{s.padding}</td>
            <td className="text-center">{s.active? '✓':''}</td>
            <td className="text-right px-2 py-1"><button className="px-2 py-1 rounded border" onClick={()=>{ setEditingId(s.id); setForm({ doc_type:s.doc_type, prefix:s.prefix, next_number:s.next_number, padding:s.padding, active:s.active }) }}>{t('edit')}</button></td>
          </tr>
        ))}
      </tbody></table>
    </div>
  )
}

function SmtpTab(){
  const { t } = useTranslation()
  const [cfg, setCfg] = React.useState<SmtpConfig>({ server:'', port:587, use_tls:true, use_ssl:false, username:'', password:'' })
  const [loading, setLoading] = React.useState(false)
  const [testEmail, setTestEmail] = React.useState('')
  const [diag, setDiag] = React.useState<any | null>(null)
  React.useEffect(()=>{ (async ()=>{ setLoading(true); try{ const c = await getSmtpConfig(); if (c) setCfg({ ...cfg, ...c }) } finally { setLoading(false) } })() }, [])
  const save = async (e: React.FormEvent)=>{ e.preventDefault(); setLoading(true); try{ const body: any = { ...cfg }; if (!body.password) delete body.password; const saved = await updateSmtpConfig(body); setCfg({ ...cfg, ...saved, password: '' }) } finally { setLoading(false) } }
  return (
    <div>
      <SectionHeader title={(t('smtp_settings') as string) || 'SMTP'} onReload={()=>{}} />
      <form onSubmit={save} className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <input placeholder={(t('server') as string) || 'Server'} value={cfg.server} onChange={e=>setCfg({...cfg, server:e.target.value})} className="input" />
        <input type="number" placeholder={(t('port') as string) || 'Port'} value={cfg.port} onChange={e=>setCfg({...cfg, port:Number(e.target.value)})} className="input" />
        <label className="flex items-center gap-2"><input type="checkbox" checked={!!cfg.use_tls} onChange={e=>setCfg({...cfg, use_tls:e.target.checked})} />TLS</label>
        <label className="flex items-center gap-2"><input type="checkbox" checked={!!cfg.use_ssl} onChange={e=>setCfg({...cfg, use_ssl:e.target.checked})} />SSL</label>
        <input placeholder={(t('username') as string) || 'Username'} value={cfg.username||''} onChange={e=>setCfg({...cfg, username:e.target.value})} className="input" />
        <input type="password" placeholder={(t('password') as string) || 'Password'} value={cfg.password||''} onChange={e=>setCfg({...cfg, password:e.target.value})} className="input" />
  {/* From fields removed as per requirements; sender will be the SMTP username */}
        <div className="col-span-2 md:col-span-4 flex flex-wrap items-center justify-between gap-2">
          <button type="button" disabled={loading} className="px-3 py-1 rounded border" onClick={async()=>{
            setLoading(true); setDiag(null);
            try {
              const d = await diagnoseSmtp();
              setDiag(d);
            } catch (e:any) {
              setDiag({ error: e?.response?.data?.error || e?.message || String(e) })
            } finally { setLoading(false) }
          }}>{t('diagnose')||'Diagnosticar'}</button>
          <input placeholder={(t('email') as string) || 'Email'} value={testEmail} onChange={e=>setTestEmail(e.target.value)} className="input w-64" />
          <button type="button" disabled={loading || !testEmail} className="px-3 py-1 rounded border" onClick={async()=>{
            setLoading(true);
            try {
              const j: any = await testSmtp(testEmail);
              if (j?.ok) {
                // If backend indicates a working fallback combo, persist it
                if (j?.fallback && (typeof j.fallback.port !== 'undefined')) {
                  const next: any = { ...cfg, use_ssl: !!j.fallback.use_ssl, use_tls: !!j.fallback.use_tls, port: Number(j.fallback.port)||cfg.port };
                  if (!next.password) delete next.password;
                  try { const saved = await updateSmtpConfig(next); setCfg({ ...cfg, ...saved, password: '' }); } catch {}
                }
                alert(t('smtp_ok') as string);
              } else {
                alert(`${t('smtp_error')}: ${j?.error||''}`);
              }
            } catch (e:any) {
              const msg = e?.response?.data?.error || e?.message || '';
              alert(`${t('smtp_error')}: ${msg}`);
            } finally { setLoading(false) }
          }}> {t('test')||'Testar'} </button>
          <button disabled={loading} className="btn btn-primary">{t('save') as string}</button>
        </div>
        {diag && (
          <div className="col-span-2 md:col-span-4 mt-3">
            <div className="text-sm font-medium mb-1">{t('diagnose_report')||'Diagnóstico'}</div>
            <pre className="text-xs whitespace-pre-wrap bg-gray-50 p-2 rounded border max-h-80 overflow-auto">{JSON.stringify(diag, null, 2)}</pre>
          </div>
        )}
      </form>
    </div>
  )
}
