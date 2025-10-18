import React from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '@/context/AuthContext'
import {
  listClients, createClient, updateClient, deleteClient, type Client,
  listCurrencies, listPaymentTypes, listPaymentForms, listPaymentMethods,
  listCountries, type Country, type ShippingAddress,
  listClientShippingAddresses, createClientShippingAddress, updateClientShippingAddress, deleteClientShippingAddress,
  type ClientPrice, listClientPrices, createClientPrice, updateClientPrice, deleteClientPrice
} from '@/api/masterdata'
import { listServices, type Service } from '@/api/masterdata'

function SectionHeader({ title, onReload }: { title: string, onReload: ()=>void }){
  const { t } = useTranslation()
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-base font-semibold text-gray-800">{title}</h2>
      <button onClick={onReload} className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors">{t('reload')}</button>
    </div>
  )
}

function Modal({ open, title, children, onClose }: { open: boolean; title: string; children: React.ReactNode; onClose: ()=>void }){
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-[95vw] md:max-w-5xl p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
          <button onClick={onClose} className="px-2 py-1 text-gray-500 hover:text-gray-700 transition-colors text-xl">✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export default function ClientsManager(){
  const { t } = useTranslation()
  const { preferences, setPreference } = useAuth()
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

  // Countries
  const [countries, setCountries] = React.useState<Country[]>([])
  React.useEffect(()=>{ (async ()=>{
    try{
      const cs = await listCountries(); setCountries(cs.items||[])
    } catch{}
  })() }, [])

  const totalPages = Math.max(1, Math.ceil(total/20))
  // Create modal state
  const [creating, setCreating] = React.useState<boolean>(false)
  const [createForm, setCreateForm] = React.useState<Partial<Client>>({})
  const [createErr, setCreateErr] = React.useState<string>('')
  const openCreate = ()=>{ setCreateForm({}); setCreateErr(''); setCreating(true) }
  const closeCreate = ()=>{ setCreating(false); setCreateErr(''); setCreateForm({}) }
  // Create-modal Envio: pending in-memory lists (saved after client is created)
  const [showEnvioCreate, setShowEnvioCreate] = React.useState<boolean>(true)
  const [envTabCreate, setEnvTabCreate] = React.useState<'prices'|'addresses'>('prices')
  const [pendingAddrs, setPendingAddrs] = React.useState<ShippingAddress[]>([])
  const [pendingAddrForm, setPendingAddrForm] = React.useState<Partial<ShippingAddress>>({ code:'', address1:'', address2:'', postal_code:'', city:'', country_code:'' })
  const [pendingAddrEditIdx, setPendingAddrEditIdx] = React.useState<number | null>(null)
  const [pendingPrices, setPendingPrices] = React.useState<ClientPrice[]>([])
  const [pendingPriceForm, setPendingPriceForm] = React.useState<Partial<ClientPrice>>({ sale_type:'', sale_code:'', code:'', uom:'', min_qty:1, unit_price:0, start_date:'', end_date:'' })
  const [pendingPriceEditIdx, setPendingPriceEditIdx] = React.useState<number | null>(null)
  const [createDefaultShipCode, setCreateDefaultShipCode] = React.useState<string>('')
  // Service autocomplete for price code (create modal)
  const [pendingPriceSvcQ, setPendingPriceSvcQ] = React.useState<string>('')
  const [pendingPriceSvcOpts, setPendingPriceSvcOpts] = React.useState<Service[]>([])
  React.useEffect(()=>{
    const h = setTimeout(async ()=>{
      if (!pendingPriceSvcQ) { setPendingPriceSvcOpts([]); return }
      try { const { items } = await listServices(pendingPriceSvcQ, 1, 10); setPendingPriceSvcOpts(items as any) } catch { setPendingPriceSvcOpts([]) }
    }, 300)
    return ()=> clearTimeout(h)
  }, [pendingPriceSvcQ])
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
      // 1) create client
      const created = await createClient(body)
      const cid = created.id as string
      // 2) create pending shipping addresses for this client
      for (const a of pendingAddrs){
        try{
          await createClientShippingAddress(cid, { ...a, country_code: (a.country_code||'').toUpperCase() })
        }catch(ex:any){
          console.warn('Failed creating address for client', ex)
        }
      }
      // 3) set default shipping address if selected and exists among pending
      if (createDefaultShipCode){
        try { await updateClient(cid, { default_shipping_address: createDefaultShipCode }) } catch(ex:any){ console.warn('Failed setting default shipping', ex) }
      }
      // 4) create pending prices for this client
      for (const p of pendingPrices){
        try{
          await createClientPrice(cid, {
            ...p,
            min_qty: Number.isFinite(Number(p.min_qty)) ? Number(p.min_qty) : 1,
            unit_price: Number.isFinite(Number(p.unit_price)) ? Number(p.unit_price) : 0,
          })
        }catch(ex:any){
          console.warn('Failed creating client price', ex)
        }
      }
      // Done
      closeCreate();
      // reset pending state
      setPendingAddrs([]); setPendingAddrForm({ code:'', address1:'', address2:'', postal_code:'', city:'', country_code:'' }); setPendingAddrEditIdx(null)
      setPendingPrices([]); setPendingPriceForm({ sale_type:'', sale_code:'', code:'', uom:'', min_qty:1, unit_price:0, start_date:'', end_date:'' }); setPendingPriceEditIdx(null)
      setCreateDefaultShipCode('')
      reload()
    } catch(e:any){ setCreateErr(e?.response?.data?.error || e?.message || 'Error') }
  }

  // Client-scoped shipping addresses management (inside Edit modal)
  const [clientAddrs, setClientAddrs] = React.useState<ShippingAddress[]>([])
  const [showEnvio, setShowEnvio] = React.useState<boolean>(true)
  const [envTab, setEnvTab] = React.useState<'prices'|'addresses'>('prices')
  const [addrForm, setAddrForm] = React.useState<Partial<ShippingAddress>>({ code:'', address1:'', address2:'', postal_code:'', city:'', country_code:'' })
  const [addrEditingId, setAddrEditingId] = React.useState<string>('')
  const [addrErr, setAddrErr] = React.useState<string>('')
  const loadClientAddrs = React.useCallback(async (cid: string)=>{
    try { const { items } = await listClientShippingAddresses(cid); setClientAddrs(items||[]) } catch { setClientAddrs([]) }
  }, [])

  // Client-specific prices (inside Edit modal > Envio > Preços)
  const [clientPrices, setClientPrices] = React.useState<ClientPrice[]>([])
  const [priceForm, setPriceForm] = React.useState<Partial<ClientPrice>>({ sale_type:'', sale_code:'', code:'', uom:'', min_qty:1, unit_price:0, start_date:'', end_date:'' })
  const [priceEditingId, setPriceEditingId] = React.useState<string>('')
  const [priceErr, setPriceErr] = React.useState<string>('')
  const loadClientPrices = React.useCallback(async (cid: string)=>{
    try { const { items } = await listClientPrices(cid); setClientPrices(items||[]) } catch { setClientPrices([]) }
  }, [])
  // Service autocomplete for price code (edit modal)
  const [priceSvcQ, setPriceSvcQ] = React.useState<string>('')
  const [priceSvcOpts, setPriceSvcOpts] = React.useState<Service[]>([])
  React.useEffect(()=>{
    const h = setTimeout(async ()=>{
      if (!priceSvcQ) { setPriceSvcOpts([]); return }
      try { const { items } = await listServices(priceSvcQ, 1, 10); setPriceSvcOpts(items as any) } catch { setPriceSvcOpts([]) }
    }, 300)
    return ()=> clearTimeout(h)
  }, [priceSvcQ])

  // Whenever we open the edit modal, load that client's shipping addresses
  React.useEffect(()=>{
    if (editing?.id) { loadClientAddrs(editing.id); loadClientPrices(editing.id) }
  }, [editing?.id, loadClientAddrs, loadClientPrices])

  return (
    <div className="space-y-4">
      <SectionHeader title={t('clients') as string} onReload={reload} />
      <div className="flex items-center gap-3 mb-4">
        <input value={q} onChange={e=>{ setQ(e.target.value); setPage(1) }} placeholder={t('search') as string} className="input flex-1 max-w-md" />
        {loading && <span className="text-sm text-gray-500">A carregar...</span>}
        <div className="ml-auto flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              checked={!!preferences?.wideForm}
              onChange={(e)=> setPreference('wideForm', e.target.checked)}
              className="rounded"
            />
            {t('wide_form') as string || 'Formulário Largo'}
          </label>
          <button type="button" onClick={openCreate} className="btn btn-primary">{t('create') as string}</button>
        </div>
      </div>
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">{t('name')}</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">{t('email')}</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">{t('phone')}</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">{t('tax_id')}</th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Ações</th>
            </tr>
          </thead>
        <tbody>
          {items.map((c:any)=> (
            <tr key={c.id} className="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
              <td className="py-3 px-4 text-sm text-gray-900 dark:text-gray-100">{(c.first_name||c.last_name)? `${c.first_name||''} ${c.last_name||''}`.trim() : c.name}</td>
              <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">{c.email||'—'}</td>
              <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">{c.phone||'—'}</td>
              <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">{c.tax_id||'—'}</td>
              <td className="py-3 px-4 text-right">
                <div className="flex gap-2 justify-end">
                  <button onClick={()=>openEdit(c)} className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors">{t('edit')}</button>
                  <button onClick={()=>remove(c.id as string)} className="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors">{t('remove')}</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      <div className="flex items-center justify-between mt-4">
        <div className="text-sm text-gray-600">{t('list')}: <span className="font-semibold">{total}</span></div>
        <div className="flex gap-2">
          <button disabled={page<=1} onClick={()=>setPage(p=>Math.max(1,p-1))} className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">«</button>
          <div className="px-4 py-1.5 text-sm font-medium">{page} / {totalPages}</div>
          <button disabled={page>=totalPages} onClick={()=>setPage(p=>Math.min(totalPages,p+1))} className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">»</button>
        </div>
      </div>

      <Modal open={!!editing} title={t('edit') as string} onClose={closeEdit}>
        {editErr && <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{editErr}</div>}
        <form onSubmit={saveEdit} className={`grid grid-cols-2 ${preferences?.wideForm ? 'md:grid-cols-8' : 'md:grid-cols-6'} gap-3`}>
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
          <div className="col-span-2 md:col-span-3 flex gap-2 items-center">
            <select value={(editForm as any).default_shipping_address || ''} onChange={e=>setEditForm({...editForm, default_shipping_address: e.target.value})} className="input w-full">
              <option value="">{t('default_shipping_address') as string || 'Endereço Envio (predef.)'}</option>
              {clientAddrs.map(a=> (<option key={a.id} value={a.code}>{a.code} - {a.address1}</option>))}
            </select>
            <button
              type="button"
              title={(t('shipping') as string) || 'Envio'}
              className={`px-2 py-1 rounded border whitespace-nowrap ${showEnvio ? 'bg-gray-100 dark:bg-gray-800' : ''}`}
              onClick={()=>setShowEnvio(s=>!s)}
            >
              {(t('shipping') as string) || 'Envio'}
            </button>
          </div>
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
          <div className="col-span-2 md:col-span-6 flex justify-end gap-2">
            <button type="button" onClick={closeEdit} className="px-3 py-1 rounded border">{t('cancel')}</button>
            <button type="submit" className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('save')}</button>
          </div>
        </form>

        {/* Envio: subsections (Preços, Endereços de Envio) */}
        {showEnvio && editing?.id && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex gap-2">
                <button type="button" onClick={()=>setEnvTab('prices')} className={`px-3 py-1 rounded border ${envTab==='prices' ? 'bg-gray-900 text-white dark:bg-gray-700' : ''}`}>{(t('prices') as string) || 'Preços'}</button>
                <button type="button" onClick={()=>setEnvTab('addresses')} className={`px-3 py-1 rounded border ${envTab==='addresses' ? 'bg-gray-900 text-white dark:bg-gray-700' : ''}`}>{(t('shipping_addresses') as string) || 'Endereços de Envio'}</button>
              </div>
              <div className="text-sm opacity-70">{(t('client_number') as string) || 'Número Cliente'}: {editing?.code || ''}</div>
            </div>

            {envTab === 'prices' && (
              <div>
                {priceErr && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{priceErr}</div>}
                <form onSubmit={async (e)=>{
                  e.preventDefault(); if (!editing?.id) return; setPriceErr('')
                  try {
                    const payload = {
                      ...priceForm,
                      min_qty: Number.isFinite(Number(priceForm.min_qty)) ? Number(priceForm.min_qty) : 1,
                      unit_price: Number.isFinite(Number(priceForm.unit_price)) ? Number(priceForm.unit_price) : 0,
                    }
                    if (priceEditingId) {
                      await updateClientPrice(editing.id, priceEditingId, payload)
                      setPriceEditingId('')
                    } else {
                      await createClientPrice(editing.id, payload)
                    }
                    setPriceForm({ sale_type:'', sale_code:'', code:'', uom:'', min_qty:1, unit_price:0, start_date:'', end_date:'' })
                    loadClientPrices(editing.id)
                  } catch(e:any) { setPriceErr(e?.response?.data?.error || e?.message || 'Error') }
                }} className="grid grid-cols-2 md:grid-cols-8 gap-2 mb-2">
                  <select value={String(priceForm.sale_type||'')} onChange={e=>setPriceForm({...priceForm, sale_type:e.target.value})} className="input col-span-2 md:col-span-2">
                    <option value="">{(t('sale_type') as string) || 'Tipo de Venda'}</option>
                    <option value="service">Service</option>
                    <option value="product">Product</option>
                  </select>
                  <input placeholder={(t('sale_code') as string) || 'Código Venda'} value={String(priceForm.sale_code||'')} onChange={e=>setPriceForm({...priceForm, sale_code:e.target.value})} className="input col-span-2 md:col-span-2" />
                  <div className="relative col-span-2 md:col-span-3">
                    <input placeholder={(t('code') as string) || 'Código'} value={String(priceForm.code||'')} onChange={e=>{ setPriceForm({...priceForm, code:e.target.value}); if ((priceForm.sale_type||'')==='service') setPriceSvcQ(e.target.value) }} className="input w-full" />
                    {(priceForm.sale_type==='service' && priceSvcOpts.length>0) && (
                      <div className="absolute left-0 mt-1 z-20 bg-white dark:bg-gray-900 border w-[40rem] max-w-[95vw] max-h-80 overflow-auto shadow-lg rounded-md">
                        {priceSvcOpts.map((s:any)=> (
                          <div key={s.id as string} className="px-2 py-1 hover:bg-gray-100 cursor-pointer flex items-center justify-between" onClick={()=>{ setPriceForm(prev=>({...prev, sale_type:'service', code:s.code||'' })); setPriceSvcQ(''); setPriceSvcOpts([]) }}>
                            <div className="truncate">{s.code? `${s.code} — ${s.name}`: s.name}</div>
                            <div className="text-xs opacity-70 ml-2 whitespace-nowrap">{s.price!=null? Number(s.price).toFixed(2): ''}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <input placeholder={(t('uom') as string) || 'Unidade Medida'} value={String(priceForm.uom||'')} onChange={e=>setPriceForm({...priceForm, uom:e.target.value})} className="input col-span-1 md:col-span-1" />
                  <input type="number" step="1" min={1} placeholder={(t('min_qty') as string) || 'Quantidade Minima'} value={String(priceForm.min_qty ?? 1)} onChange={e=>setPriceForm({...priceForm, min_qty: Number(e.target.value) })} className="input col-span-1 md:col-span-1" />
                  <input type="number" step="0.01" placeholder={(t('unit_price') as string) || 'Preço Unitário'} value={String(priceForm.unit_price ?? 0)} onChange={e=>setPriceForm({...priceForm, unit_price: Number(e.target.value) })} className="input col-span-1 md:col-span-1" />
                  <input type="date" placeholder={(t('start_date') as string) || 'Data Inicio'} value={String(priceForm.start_date||'')} onChange={e=>setPriceForm({...priceForm, start_date:e.target.value})} className="input col-span-1 md:col-span-1" />
                  <input type="date" placeholder={(t('end_date') as string) || 'Data Fim'} value={String(priceForm.end_date||'')} onChange={e=>setPriceForm({...priceForm, end_date:e.target.value})} className="input col-span-1 md:col-span-1" />
                  <button className="btn btn-primary col-span-2 md:col-span-1">{priceEditingId ? (t('save') as string) : (t('create') as string)}</button>
                </form>
                <table className="w-full text-sm"><thead><tr>
                  <th>{(t('sale_type') as string) || 'Tipo de Venda'}</th>
                  <th>{(t('sale_code') as string) || 'Código Venda'}</th>
                  <th>{t('code') || 'Código'}</th>
                  <th>{(t('uom') as string) || 'Unidade Medida'}</th>
                  <th>{(t('min_qty') as string) || 'Quantidade Minima'}</th>
                  <th>{(t('unit_price') as string) || 'Preço Unitário'}</th>
                  <th>{(t('start_date') as string) || 'Data Inicio'}</th>
                  <th>{(t('end_date') as string) || 'Data Fim'}</th>
                  <th></th>
                </tr></thead><tbody>
                  {clientPrices.map((p:any)=> (
                    <tr key={p.id} className="border-t">
                      <td className="text-center">{p.sale_type}</td>
                      <td className="text-center">{p.sale_code}</td>
                      <td className="text-center">{p.code}</td>
                      <td className="text-center">{p.uom}</td>
                      <td className="text-center">{p.min_qty}</td>
                      <td className="text-center">{typeof p.unit_price==='number' ? p.unit_price.toFixed(2) : p.unit_price}</td>
                      <td className="text-center">{p.start_date}</td>
                      <td className="text-center">{p.end_date}</td>
                      <td className="text-right px-2 py-1 flex gap-2 justify-end">
                        <button type="button" className="text-blue-600" onClick={()=>{ setPriceEditingId(p.id as string); setPriceForm({ sale_type:p.sale_type, sale_code:p.sale_code, code:p.code, uom:p.uom, min_qty:p.min_qty, unit_price:p.unit_price, start_date:p.start_date, end_date:p.end_date }) }}>{t('edit')}</button>
                        <button type="button" className="text-red-600" onClick={async()=>{ if (!editing?.id) return; await deleteClientPrice(editing.id, p.id as string); loadClientPrices(editing.id) }}>{t('remove')}</button>
                      </td>
                    </tr>
                  ))}
                </tbody></table>
              </div>
            )}

            {envTab === 'addresses' && (
              <div>
                <div className="text-sm font-semibold mb-2">{t('shipping_addresses') as string || 'Shipping Addresses'}</div>
                {addrErr && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{addrErr}</div>}
                <form onSubmit={async (e)=>{
                  e.preventDefault(); if (!editing?.id) return; setAddrErr('')
                  try {
                    const payload = { ...addrForm, country_code: (addrForm.country_code||'').toUpperCase() }
                    if (addrEditingId) {
                      await updateClientShippingAddress(editing.id, addrEditingId, payload)
                      setAddrEditingId('')
                    } else {
                      await createClientShippingAddress(editing.id, payload)
                    }
                    setAddrForm({ code:'', address1:'', address2:'', postal_code:'', city:'', country_code:'' })
                    loadClientAddrs(editing.id)
                  } catch(e:any) { setAddrErr(e?.response?.data?.error || e?.message || 'Error') }
                }} className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2">
                  <input placeholder={(t('code') as string)||'Code'} value={String(addrForm.code||'')} onChange={e=>setAddrForm({...addrForm, code:e.target.value})} className="input" />
                  <input placeholder={(t('address1') as string)||'Address 1'} value={String(addrForm.address1||'')} onChange={e=>setAddrForm({...addrForm, address1:e.target.value})} className="input col-span-2" />
                  <input placeholder={(t('address2') as string)||'Address 2'} value={String(addrForm.address2||'')} onChange={e=>setAddrForm({...addrForm, address2:e.target.value})} className="input col-span-2" />
                  <input placeholder={(t('postal_code') as string)||'Postal Code'} value={String(addrForm.postal_code||'')} onChange={e=>setAddrForm({...addrForm, postal_code:e.target.value})} className="input" />
                  <input placeholder={(t('city') as string)||'City'} value={String(addrForm.city||'')} onChange={e=>setAddrForm({...addrForm, city:e.target.value})} className="input" />
                  <select value={String(addrForm.country_code||'')} onChange={e=>setAddrForm({...addrForm, country_code:e.target.value})} className="input">
                    <option value="">{(t('country') as string)||'Country'}</option>
                    {countries.map(c=> (<option key={c.id} value={c.code}>{c.code} - {c.name}</option>))}
                  </select>
                  <button className="btn btn-primary">{addrEditingId ? (t('save') as string) : (t('create') as string)}</button>
                </form>
                <table className="w-full text-sm"><thead><tr>
                  <th>{t('code')}</th><th>{t('address1')||'Address 1'}</th><th>{t('postal_code')||'Postal Code'}</th><th>{t('city')||'City'}</th><th>{t('country')||'Country'}</th><th></th>
                </tr></thead><tbody>
                  {clientAddrs.map((a:any)=> (
                    <tr key={a.id} className="border-t">
                      <td className="text-center">{a.code}</td>
                      <td className="text-center">{a.address1}</td>
                      <td className="text-center">{a.postal_code}</td>
                      <td className="text-center">{a.city}</td>
                      <td className="text-center">{a.country_code}</td>
                      <td className="text-right px-2 py-1 flex gap-2 justify-end">
                        <button type="button" className="text-blue-600" onClick={()=>{ setAddrEditingId(a.id as string); setAddrForm({ code:a.code, address1:a.address1, address2:a.address2, postal_code:a.postal_code, city:a.city, country_code:a.country_code }) }}>{t('edit')}</button>
                        <button type="button" className="text-red-600" onClick={async()=>{ if (!editing?.id) return; await deleteClientShippingAddress(editing.id, a.id as string); loadClientAddrs(editing.id) }}>{t('remove')}</button>
                      </td>
                    </tr>
                  ))}
                </tbody></table>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Create modal with Envio subtabs (pending items saved right after client creation) */}
      <Modal open={creating} title={t('create') as string} onClose={closeCreate}>
        {createErr && <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm border border-red-200">{createErr}</div>}
        <form onSubmit={saveCreate} className={`grid grid-cols-2 ${preferences?.wideForm ? 'md:grid-cols-8' : 'md:grid-cols-6'} gap-3`}>
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
          {/* Default shipping address from pending addresses */}
          <div className="col-span-2 md:col-span-2 flex gap-2 items-center">
            <select value={createDefaultShipCode} onChange={e=>setCreateDefaultShipCode(e.target.value)} className="input w-full">
              <option value="">{t('default_shipping_address') as string || 'Endereço Envio (predef.)'}</option>
              {pendingAddrs.map((a, idx)=> (<option key={idx} value={a.code||''}>{a.code} - {a.address1}</option>))}
            </select>
            <button type="button" className={`px-2 py-1 rounded border whitespace-nowrap ${showEnvioCreate ? 'bg-gray-100 dark:bg-gray-800':''}`} onClick={()=>setShowEnvioCreate(s=>!s)}>
              {(t('shipping') as string) || 'Envio'}
            </button>
          </div>
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

        {showEnvioCreate && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex gap-2">
                <button type="button" onClick={()=>setEnvTabCreate('prices')} className={`px-3 py-1 rounded border ${envTabCreate==='prices' ? 'bg-gray-900 text-white dark:bg-gray-700' : ''}`}>{(t('prices') as string) || 'Preços'}</button>
                <button type="button" onClick={()=>setEnvTabCreate('addresses')} className={`px-3 py-1 rounded border ${envTabCreate==='addresses' ? 'bg-gray-900 text-white dark:bg-gray-700' : ''}`}>{(t('shipping_addresses') as string) || 'Endereços de Envio'}</button>
              </div>
              {/* Número Cliente não existe ainda no create */}
              <div className="text-sm opacity-70">{(t('client_number') as string) || 'Número Cliente'}: —</div>
            </div>

            {envTabCreate === 'prices' && (
              <div>
                <form onSubmit={(e)=>{ e.preventDefault(); const item = {
                  sale_type: String(pendingPriceForm.sale_type||''),
                  sale_code: String(pendingPriceForm.sale_code||''),
                  code: String(pendingPriceForm.code||''),
                  uom: String(pendingPriceForm.uom||''),
                  min_qty: Number.isFinite(Number(pendingPriceForm.min_qty)) ? Number(pendingPriceForm.min_qty) : 1,
                  unit_price: Number.isFinite(Number(pendingPriceForm.unit_price)) ? Number(pendingPriceForm.unit_price) : 0,
                  start_date: pendingPriceForm.start_date||'',
                  end_date: pendingPriceForm.end_date||''
                } as ClientPrice; if(pendingPriceEditIdx!==null){ const copy=[...pendingPrices]; copy[pendingPriceEditIdx]=item; setPendingPrices(copy); setPendingPriceEditIdx(null); } else { setPendingPrices(prev=>[...prev,item]); } setPendingPriceForm({ sale_type:'', sale_code:'', code:'', uom:'', min_qty:1, unit_price:0, start_date:'', end_date:'' }) }} className="grid grid-cols-2 md:grid-cols-8 gap-2 mb-2">
                  <select value={String(pendingPriceForm.sale_type||'')} onChange={e=>setPendingPriceForm({...pendingPriceForm, sale_type:e.target.value})} className="input col-span-2 md:col-span-2">
                    <option value="">{(t('sale_type') as string) || 'Tipo de Venda'}</option>
                    <option value="service">Service</option>
                    <option value="product">Product</option>
                  </select>
                  <input placeholder={(t('sale_code') as string) || 'Código Venda'} value={String(pendingPriceForm.sale_code||'')} onChange={e=>setPendingPriceForm({...pendingPriceForm, sale_code:e.target.value})} className="input col-span-2 md:col-span-2" />
                  <div className="relative col-span-2 md:col-span-3">
                    <input placeholder={(t('code') as string) || 'Código'} value={String(pendingPriceForm.code||'')} onChange={e=>{ setPendingPriceForm({...pendingPriceForm, code:e.target.value}); if ((pendingPriceForm.sale_type||'')==='service') setPendingPriceSvcQ(e.target.value) }} className="input w-full" />
                    {(pendingPriceForm.sale_type==='service' && pendingPriceSvcOpts.length>0) && (
                      <div className="absolute left-0 mt-1 z-20 bg-white dark:bg-gray-900 border w-[40rem] max-w-[95vw] max-h-80 overflow-auto shadow-lg rounded-md">
                        {pendingPriceSvcOpts.map((s:any)=> (
                          <div key={s.id as string} className="px-2 py-1 hover:bg-gray-100 cursor-pointer flex items-center justify-between" onClick={()=>{ setPendingPriceForm(prev=>({...prev, sale_type:'service', code:s.code||'' })); setPendingPriceSvcQ(''); setPendingPriceSvcOpts([]) }}>
                            <div className="truncate">{s.code? `${s.code} — ${s.name}`: s.name}</div>
                            <div className="text-xs opacity-70 ml-2 whitespace-nowrap">{s.price!=null? Number(s.price).toFixed(2): ''}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <input placeholder={(t('uom') as string) || 'Unidade Medida'} value={String(pendingPriceForm.uom||'')} onChange={e=>setPendingPriceForm({...pendingPriceForm, uom:e.target.value})} className="input col-span-1 md:col-span-1" />
                  <input type="number" step="1" min={1} placeholder={(t('min_qty') as string) || 'Quantidade Minima'} value={String(pendingPriceForm.min_qty ?? 1)} onChange={e=>setPendingPriceForm({...pendingPriceForm, min_qty: Number(e.target.value) })} className="input col-span-1 md:col-span-1" />
                  <input type="number" step="0.01" placeholder={(t('unit_price') as string) || 'Preço Unitário'} value={String(pendingPriceForm.unit_price ?? 0)} onChange={e=>setPendingPriceForm({...pendingPriceForm, unit_price: Number(e.target.value) })} className="input col-span-1 md:col-span-1" />
                  <input type="date" placeholder={(t('start_date') as string) || 'Data Inicio'} value={String(pendingPriceForm.start_date||'')} onChange={e=>setPendingPriceForm({...pendingPriceForm, start_date:e.target.value})} className="input col-span-1 md:col-span-1" />
                  <input type="date" placeholder={(t('end_date') as string) || 'Data Fim'} value={String(pendingPriceForm.end_date||'')} onChange={e=>setPendingPriceForm({...pendingPriceForm, end_date:e.target.value})} className="input col-span-1 md:col-span-1" />
                  <button className="btn btn-primary col-span-2 md:col-span-1">{pendingPriceEditIdx!==null ? (t('save') as string) : (t('create') as string)}</button>
                </form>
                <table className="w-full text-sm"><thead><tr>
                  <th>{(t('sale_type') as string) || 'Tipo de Venda'}</th>
                  <th>{(t('sale_code') as string) || 'Código Venda'}</th>
                  <th>{t('code') || 'Código'}</th>
                  <th>{(t('uom') as string) || 'Unidade Medida'}</th>
                  <th>{(t('min_qty') as string) || 'Quantidade Minima'}</th>
                  <th>{(t('unit_price') as string) || 'Preço Unitário'}</th>
                  <th>{(t('start_date') as string) || 'Data Inicio'}</th>
                  <th>{(t('end_date') as string) || 'Data Fim'}</th>
                  <th></th>
                </tr></thead><tbody>
                  {pendingPrices.map((p, idx)=> (
                    <tr key={idx} className="border-t">
                      <td className="text-center">{p.sale_type}</td>
                      <td className="text-center">{p.sale_code}</td>
                      <td className="text-center">{p.code}</td>
                      <td className="text-center">{p.uom}</td>
                      <td className="text-center">{p.min_qty}</td>
                      <td className="text-center">{typeof p.unit_price==='number' ? p.unit_price.toFixed(2) : p.unit_price}</td>
                      <td className="text-center">{p.start_date as any}</td>
                      <td className="text-center">{p.end_date as any}</td>
                      <td className="text-right px-2 py-1 flex gap-2 justify-end">
                        <button type="button" className="text-blue-600" onClick={()=>{ setPendingPriceEditIdx(idx); setPendingPriceForm({ ...p }) }}>{t('edit')}</button>
                        <button type="button" className="text-red-600" onClick={()=>{ setPendingPrices(prev=>prev.filter((_,i)=>i!==idx)) }}>{t('remove')}</button>
                      </td>
                    </tr>
                  ))}
                </tbody></table>
              </div>
            )}

            {envTabCreate === 'addresses' && (
              <div>
                <form onSubmit={(e)=>{ e.preventDefault(); const item = {
                  code: String(pendingAddrForm.code||''),
                  address1: String(pendingAddrForm.address1||''),
                  address2: String(pendingAddrForm.address2||''),
                  postal_code: String(pendingAddrForm.postal_code||''),
                  city: String(pendingAddrForm.city||''),
                  country_code: String(pendingAddrForm.country_code||'').toUpperCase(),
                } as ShippingAddress; if(pendingAddrEditIdx!==null){ const copy=[...pendingAddrs]; copy[pendingAddrEditIdx]=item; setPendingAddrs(copy); setPendingAddrEditIdx(null); } else { setPendingAddrs(prev=>[...prev,item]); } setPendingAddrForm({ code:'', address1:'', address2:'', postal_code:'', city:'', country_code:'' }) }} className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2">
                  <input placeholder={(t('code') as string)||'Code'} value={String(pendingAddrForm.code||'')} onChange={e=>setPendingAddrForm({...pendingAddrForm, code:e.target.value})} className="input" />
                  <input placeholder={(t('address1') as string)||'Address 1'} value={String(pendingAddrForm.address1||'')} onChange={e=>setPendingAddrForm({...pendingAddrForm, address1:e.target.value})} className="input col-span-2" />
                  <input placeholder={(t('address2') as string)||'Address 2'} value={String(pendingAddrForm.address2||'')} onChange={e=>setPendingAddrForm({...pendingAddrForm, address2:e.target.value})} className="input col-span-2" />
                  <input placeholder={(t('postal_code') as string)||'Postal Code'} value={String(pendingAddrForm.postal_code||'')} onChange={e=>setPendingAddrForm({...pendingAddrForm, postal_code:e.target.value})} className="input" />
                  <input placeholder={(t('city') as string)||'City'} value={String(pendingAddrForm.city||'')} onChange={e=>setPendingAddrForm({...pendingAddrForm, city:e.target.value})} className="input" />
                  <select value={String(pendingAddrForm.country_code||'')} onChange={e=>setPendingAddrForm({...pendingAddrForm, country_code:e.target.value})} className="input">
                    <option value="">{(t('country') as string)||'Country'}</option>
                    {countries.map(c=> (<option key={c.id} value={c.code}>{c.code} - {c.name}</option>))}
                  </select>
                  <button className="btn btn-primary">{pendingAddrEditIdx!==null ? (t('save') as string) : (t('create') as string)}</button>
                </form>
                <table className="w-full text-sm"><thead><tr>
                  <th>{t('code')}</th><th>{t('address1')||'Address 1'}</th><th>{t('postal_code')||'Postal Code'}</th><th>{t('city')||'City'}</th><th>{t('country')||'Country'}</th><th></th>
                </tr></thead><tbody>
                  {pendingAddrs.map((a, idx)=> (
                    <tr key={idx} className="border-t">
                      <td className="text-center">{a.code}</td>
                      <td className="text-center">{a.address1}</td>
                      <td className="text-center">{a.postal_code}</td>
                      <td className="text-center">{a.city}</td>
                      <td className="text-center">{a.country_code}</td>
                      <td className="text-right px-2 py-1 flex gap-2 justify-end">
                        <button type="button" className="text-blue-600" onClick={()=>{ setPendingAddrEditIdx(idx); setPendingAddrForm({ ...a }) }}>{t('edit')}</button>
                        <button type="button" className="text-red-600" onClick={()=>{ setPendingAddrs(prev=>prev.filter((_,i)=>i!==idx)) }}>{t('remove')}</button>
                      </td>
                    </tr>
                  ))}
                </tbody></table>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
