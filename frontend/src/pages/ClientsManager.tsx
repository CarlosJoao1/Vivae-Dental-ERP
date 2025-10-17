import React from 'react'
import { useTranslation } from 'react-i18next'
import {
  listClients, createClient, updateClient, deleteClient, type Client,
  listCurrencies, listPaymentTypes, listPaymentForms, listPaymentMethods,
  listCountries, type Country, listShippingAddresses, type ShippingAddress
} from '@/api/masterdata'

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
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-2xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="px-2 py-1">✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export default function ClientsManager(){
  const { t } = useTranslation()
  const [q, setQ] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const [items, setItems] = React.useState<Client[]>([])
  const [page, setPage] = React.useState(1)
  const [total, setTotal] = React.useState(0)

  const reload = async ()=>{
    setLoading(true)
    try {
      const { total, items } = await listClients(q, page, 20)
      setItems(items as any)
      setTotal(total)
    } finally { setLoading(false) }
  }
  React.useEffect(()=>{ reload() }, [q, page])

  // Edit modal state
  const [editing, setEditing] = React.useState<Client | null>(null)
  const [editForm, setEditForm] = React.useState<Partial<Client>>({})
  const [editErr, setEditErr] = React.useState<string>('')

  const openEdit = (c: Client)=>{ setEditing(c); setEditForm({ ...c, preferred_currency: (c as any)?.preferred_currency?.id, payment_type: (c as any)?.payment_type?.id, payment_form: (c as any)?.payment_form?.id, payment_method: (c as any)?.payment_method?.id }) }
  const closeEdit = ()=>{ setEditing(null); setEditForm({}) }
  const saveEdit = async (e: React.FormEvent)=>{
    e.preventDefault()
    if (!editing?.id) return
    setEditErr('')
    try{
      const body: Partial<Client> = {
        ...editForm,
        country_code: (editForm.country_code||'').toUpperCase() || undefined,
      }
      if (!body.name && (body.first_name || body.last_name)) {
        const full = `${body.first_name||''} ${body.last_name||''}`.trim()
        if (full) body.name = full
      }
      await updateClient(editing.id, body)
      closeEdit(); reload()
    } catch(e:any){ setEditErr(e?.response?.data?.error || e?.message || 'Error') }
  }
  const remove = async (id: string)=>{
    if (!confirm(t('remove') as string)) return
    await deleteClient(id); reload()
  }

  // Financial lists
  const [currs, setCurrs] = React.useState<any[]>([])
  const [payTypes, setPayTypes] = React.useState<any[]>([])
  const [payForms, setPayForms] = React.useState<any[]>([])
  const [payMethods, setPayMethods] = React.useState<any[]>([])
  React.useEffect(()=>{ (async ()=>{
    try{
      const r1 = await listCurrencies(); setCurrs(r1.items||[])
      const r2 = await listPaymentTypes(); setPayTypes(r2.items||[])
      const r3 = await listPaymentForms(); setPayForms(r3.items||[])
      const r4 = await listPaymentMethods(); setPayMethods(r4.items||[])
    } catch{}
  })() }, [])

  // Countries and shipping addresses
  const [countries, setCountries] = React.useState<Country[]>([])
  const [shipAddrs, setShipAddrs] = React.useState<ShippingAddress[]>([])
  React.useEffect(()=>{ (async ()=>{
    try{
      const cs = await listCountries(); setCountries(cs.items||[])
      const sa = await listShippingAddresses(); setShipAddrs(sa.items||[])
    } catch{}
  })() }, [])

  const totalPages = Math.max(1, Math.ceil(total/20))
  // Create modal state
  const [creating, setCreating] = React.useState<boolean>(false)
  const [createForm, setCreateForm] = React.useState<Partial<Client>>({})
  const [createErr, setCreateErr] = React.useState<string>('')
  const openCreate = ()=>{ setCreateForm({}); setCreateErr(''); setCreating(true) }
  const closeCreate = ()=>{ setCreating(false); setCreateErr(''); setCreateForm({}) }
  const saveCreate = async (e: React.FormEvent)=>{
    e.preventDefault()
    setCreateErr('')
    try{
      const body: Partial<Client> = {
        ...createForm,
        country_code: (createForm.country_code||'').toUpperCase() || undefined,
      }
      if (!body.name && (body.first_name || body.last_name)) {
        const full = `${body.first_name||''} ${body.last_name||''}`.trim()
        if (full) body.name = full
      }
      if (!body.name) { throw new Error(String(t('name')) + ' ' + (String(t('required'))||'required')) }
      await createClient(body)
      closeCreate(); reload()
    } catch(e:any){ setCreateErr(e?.response?.data?.error || e?.message || 'Error') }
  }

  return (
    <div>
      <SectionHeader title={t('clients') as string} onReload={reload} />
      <div className="flex items-center gap-2 mb-3">
        <input value={q} onChange={e=>{ setQ(e.target.value); setPage(1) }} placeholder={t('search') as string} className="input" />
        {loading && <span>…</span>}
        <button type="button" onClick={openCreate} className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700 ml-auto">{t('create') as string}</button>
      </div>
      <table className="w-full text-sm">
        <thead><tr>
          <th className="text-left">{t('name')}</th>
          <th>{t('email')}</th>
          <th>{t('phone')}</th>
          <th>{t('tax_id')}</th>
          <th></th>
        </tr></thead>
        <tbody>
          {items.map((c:any)=> (
            <tr key={c.id} className="border-t">
              <td className="py-1">{(c.first_name||c.last_name)? `${c.first_name||''} ${c.last_name||''}`.trim() : c.name}</td>
              <td className="text-center">{c.email||''}</td>
              <td className="text-center">{c.phone||''}</td>
              <td className="text-center">{c.tax_id||''}</td>
              <td className="text-right flex gap-2 justify-end">
                <button onClick={()=>openEdit(c)} className="text-blue-600">{t('edit')}</button>
                <button onClick={()=>remove(c.id as string)} className="text-red-600">{t('remove')}</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center justify-between mt-3">
        <div className="text-sm">{t('list')}: {total}</div>
        <div className="flex gap-2">
          <button disabled={page<=1} onClick={()=>setPage(p=>Math.max(1,p-1))} className="px-3 py-1 rounded border">«</button>
          <div className="px-3 py-1">{page} / {totalPages}</div>
          <button disabled={page>=totalPages} onClick={()=>setPage(p=>Math.min(totalPages,p+1))} className="px-3 py-1 rounded border">»</button>
        </div>
      </div>

      <Modal open={!!editing} title={t('edit') as string} onClose={closeEdit}>
        {editErr && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{editErr}</div>}
        <form onSubmit={saveEdit} className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <input placeholder={t('first_name') as string} value={editForm.first_name || ''} onChange={e=>setEditForm({...editForm, first_name: e.target.value})} className="input" />
          <input placeholder={t('last_name') as string} value={editForm.last_name || ''} onChange={e=>setEditForm({...editForm, last_name: e.target.value})} className="input" />
          <input placeholder={t('name') as string} value={editForm.name || ''} onChange={e=>setEditForm({...editForm, name: e.target.value})} className="input col-span-2" />
          <input placeholder={t('email') as string} value={editForm.email || ''} onChange={e=>setEditForm({...editForm, email: e.target.value})} className="input" />
          <input placeholder={t('phone') as string} value={editForm.phone || ''} onChange={e=>setEditForm({...editForm, phone: e.target.value})} className="input" />
          <input placeholder={t('address') as string} value={editForm.address || ''} onChange={e=>setEditForm({...editForm, address: e.target.value})} className="input col-span-2" />
          <input placeholder={t('postal_code') as string || 'Código Postal'} value={(editForm as any).postal_code || ''} onChange={e=>setEditForm({...editForm, postal_code: e.target.value})} className="input" />
          <select value={(editForm as any).country_code || ''} onChange={e=>setEditForm({...editForm, country_code: e.target.value})} className="input">
            <option value="">{t('country') as string || 'País'}</option>
            {countries.map(c=> (<option key={c.id} value={c.code}>{c.code} - {c.name}</option>))}
          </select>
          <input placeholder={t('tax_id') as string} value={editForm.tax_id || ''} onChange={e=>setEditForm({...editForm, tax_id: e.target.value})} className="input" />
          <select value={(editForm as any).default_shipping_address || ''} onChange={e=>setEditForm({...editForm, default_shipping_address: e.target.value})} className="input">
            <option value="">{t('default_shipping_address') as string || 'Endereço Envio (predef.)'}</option>
            {shipAddrs.map(a=> (<option key={a.id} value={a.code}>{a.code} - {a.address1}</option>))}
          </select>
          <input placeholder={t('location_code') as string || 'Código Localização'} value={(editForm as any).location_code || ''} onChange={e=>setEditForm({...editForm, location_code: e.target.value})} className="input" />
          <select value={(editForm.preferred_currency as string) || ''} onChange={e=>setEditForm({...editForm, preferred_currency: e.target.value})} className="input">
            <option value="">{t('currencies')}</option>
            {currs.map(c=> (<option key={c.id} value={c.id}>{c.code} {c.name? `- ${c.name}`:''}</option>))}
          </select>
          <select value={(editForm.payment_type as string) || ''} onChange={e=>setEditForm({...editForm, payment_type: e.target.value})} className="input">
            <option value="">{t('payment_types')}</option>
            {payTypes.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <select value={(editForm.payment_form as string) || ''} onChange={e=>setEditForm({...editForm, payment_form: e.target.value})} className="input">
            <option value="">{t('payment_forms')}</option>
            {payForms.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <select value={(editForm.payment_method as string) || ''} onChange={e=>setEditForm({...editForm, payment_method: e.target.value})} className="input">
            <option value="">{t('payment_methods')}</option>
            {payMethods.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <div className="col-span-2 md:col-span-4 flex justify-end gap-2">
            <button type="button" onClick={closeEdit} className="px-3 py-1 rounded border">{t('cancel')}</button>
            <button type="submit" className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('save')}</button>
          </div>
        </form>
      </Modal>

      {/* Create modal */}
      <Modal open={creating} title={t('create') as string} onClose={closeCreate}>
        {createErr && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{createErr}</div>}
        <form onSubmit={saveCreate} className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <input placeholder={t('first_name') as string} value={createForm.first_name || ''} onChange={e=>setCreateForm({...createForm, first_name: e.target.value})} className="input" />
          <input placeholder={t('last_name') as string} value={createForm.last_name || ''} onChange={e=>setCreateForm({...createForm, last_name: e.target.value})} className="input" />
          <input placeholder={t('name') as string} value={createForm.name || ''} onChange={e=>setCreateForm({...createForm, name: e.target.value})} className="input col-span-2" />
          <input placeholder={t('email') as string} value={createForm.email || ''} onChange={e=>setCreateForm({...createForm, email: e.target.value})} className="input" />
          <input placeholder={t('phone') as string} value={createForm.phone || ''} onChange={e=>setCreateForm({...createForm, phone: e.target.value})} className="input" />
          <input placeholder={t('address') as string} value={createForm.address || ''} onChange={e=>setCreateForm({...createForm, address: e.target.value})} className="input col-span-2" />
          <input placeholder={t('postal_code') as string || 'Código Postal'} value={(createForm as any).postal_code || ''} onChange={e=>setCreateForm({...createForm, postal_code: e.target.value})} className="input" />
          <select value={(createForm as any).country_code || ''} onChange={e=>setCreateForm({...createForm, country_code: e.target.value})} className="input">
            <option value="">{t('country') as string || 'País'}</option>
            {countries.map(c=> (<option key={c.id} value={c.code}>{c.code} - {c.name}</option>))}
          </select>
          <input placeholder={t('tax_id') as string} value={createForm.tax_id || ''} onChange={e=>setCreateForm({...createForm, tax_id: e.target.value})} className="input" />
          <select value={(createForm as any).default_shipping_address || ''} onChange={e=>setCreateForm({...createForm, default_shipping_address: e.target.value})} className="input">
            <option value="">{t('default_shipping_address') as string || 'Endereço Envio (predef.)'}</option>
            {shipAddrs.map(a=> (<option key={a.id} value={a.code}>{a.code} - {a.address1}</option>))}
          </select>
          <input placeholder={t('location_code') as string || 'Código Localização'} value={(createForm as any).location_code || ''} onChange={e=>setCreateForm({...createForm, location_code: e.target.value})} className="input" />
          <select value={(createForm.preferred_currency as string) || ''} onChange={e=>setCreateForm({...createForm, preferred_currency: e.target.value})} className="input">
            <option value="">{t('currencies')}</option>
            {currs.map(c=> (<option key={c.id} value={c.id}>{c.code} {c.name? `- ${c.name}`:''}</option>))}
          </select>
          <select value={(createForm.payment_type as string) || ''} onChange={e=>setCreateForm({...createForm, payment_type: e.target.value})} className="input">
            <option value="">{t('payment_types')}</option>
            {payTypes.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <select value={(createForm.payment_form as string) || ''} onChange={e=>setCreateForm({...createForm, payment_form: e.target.value})} className="input">
            <option value="">{t('payment_forms')}</option>
            {payForms.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <select value={(createForm.payment_method as string) || ''} onChange={e=>setCreateForm({...createForm, payment_method: e.target.value})} className="input">
            <option value="">{t('payment_methods')}</option>
            {payMethods.map(p=> (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <div className="col-span-2 md:col-span-4 flex justify-end gap-2">
            <button type="button" onClick={closeCreate} className="px-3 py-1 rounded border">{t('cancel')}</button>
            <button type="submit" className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('save')}</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
