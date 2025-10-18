import React from 'react'
import { useNavigate } from 'react-router-dom'
import i18n from '@/i18n'
import { listOrders, createOrder, type Line, orderPdfUrl, sendOrderEmail, getOrder, updateOrder, convertOrderToInvoice } from '@/api/sales'
import { searchClientsBrief, type Client, listServices, type Service, getClient, listSeries, resolveClientUnitPrice } from '@/api/masterdata'
import { useTranslation } from 'react-i18next'
import { calcGross, calcNet, computeGlobalDiscount } from '@/lib/pricing'
import EmailModal, { type EmailingState } from '@/components/EmailModal'
import TotalsSummary, { GrandTotal } from '@/components/TotalsSummary'

export default function SalesOrders(){
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [items, setItems] = React.useState<any[]>([])
  const [hdr, setHdr] = React.useState({ number:'', date:'', client:'', client_name:'', currency:'EUR', notes:'', discount_rate: 0, discount_amount: 0, tax_rate: 0 })
  const [clientOpts, setClientOpts] = React.useState<Client[]>([])
  const [clientQ, setClientQ] = React.useState('')
  const [lines, setLines] = React.useState<Line[]>([{ description:'', qty:1, price:0, sale_type:'service', code:'' }])
  const [series, setSeries] = React.useState<any[]>([])
  const [seriesId, setSeriesId] = React.useState<string>('')
  const [emailing, setEmailing] = React.useState<EmailingState>(null)
  const [editing, setEditing] = React.useState<{ id:string } | null>(null)
  const [editHdr, setEditHdr] = React.useState<any>({})
  const [editLines, setEditLines] = React.useState<Line[]>([])
  const [editDiscMode, setEditDiscMode] = React.useState<Record<number,'rate'|'amount'>>({})
  const [editClientQ, setEditClientQ] = React.useState('')
  const [editClientOpts, setEditClientOpts] = React.useState<any[]>([])
  React.useEffect(()=>{ const h = setTimeout(async ()=>{ if (!editClientQ) { setEditClientOpts([]); return } const { items } = await searchClientsBrief(editClientQ); setEditClientOpts(items as any) },300); return ()=>clearTimeout(h) }, [editClientQ])
  const pickEditClient = async (c:any)=>{ setEditHdr({ ...editHdr, client: c.id, client_name: c.name }); setEditClientOpts([]); try{ const full = await getClient(c.id); const pref = (full as any)?.preferred_currency?.code; if (pref) setEditHdr((prev:any)=>({ ...prev, currency: pref })) } catch {}
  }

  const reload = async ()=>{ const { items } = await listOrders(); setItems(items) }
  React.useEffect(()=>{ reload(); (async ()=>{ const { items } = await listSeries(); setSeries(items as any) })() }, [])
  // Convert to Invoice dialog
  const [convertDlg, setConvertDlg] = React.useState<{ open: boolean; orderId?: string; seriesId?: string }>({ open: false })
  const startConvert = (orderId: string)=> setConvertDlg({ open: true, orderId, seriesId: '' })
  const doConvert = async ()=>{
    if (!convertDlg.orderId) { setConvertDlg({ open:false }); return }
    try{
      const res = await convertOrderToInvoice(convertDlg.orderId, convertDlg.seriesId ? { series: convertDlg.seriesId } : undefined)
      setConvertDlg({ open:false })
      // Navigate to invoices and open edit modal
      navigate(`/sales/invoices?open=${encodeURIComponent(res.invoice_id as any)}`)
    } catch(e:any){
      alert(e?.response?.data?.error || e?.message || 'convert error')
    }
  }

  const addLine = ()=> setLines([...lines, { description:'', qty:1, price:0, sale_type:'service', code:'' }])
  const setLine = (i:number, patch: Partial<Line>)=> setLines(lines.map((ln,idx)=> idx===i ? { ...ln, ...patch } : ln ))
  const sumGross = lines.reduce((s, ln) => s + calcGross(ln), 0)
  const sumAfterLine = lines.reduce((s, ln) => s + calcNet(ln), 0)
  const globalDisc = computeGlobalDiscount(hdr, sumAfterLine)
  const baseTax = Math.max(0, sumAfterLine - (globalDisc||0))
  const taxAmount = baseTax * ((hdr.tax_rate||0)/100)
  const grandTotal = baseTax + taxAmount

  // Client search
  React.useEffect(()=>{
    const h = setTimeout(async ()=>{
      if (!clientQ) { setClientOpts([]); return }
      const { items } = await searchClientsBrief(clientQ)
      setClientOpts(items as any)
    }, 300)
    return ()=> clearTimeout(h)
  }, [clientQ])

  const pickClient = async (c: Client)=>{
    setHdr({ ...hdr, client: (c.id as string)||'', client_name: (c.first_name || c.last_name) ? `${c.first_name||''} ${c.last_name||''}`.trim() : c.name })
    setClientOpts([])
    try {
      const full = await getClient(c.id as string)
      const pref = (full as any)?.preferred_currency?.code
      if (pref) setHdr(prev=> ({ ...prev, currency: pref }))
    } catch {}
  }

  // Service search per line
  const [svcQ, setSvcQ] = React.useState<Record<number, string>>({})
  const [svcOpts, setSvcOpts] = React.useState<Record<number, Service[]>>({})
  const onSvcChange = (i:number, q:string)=>{
    setSvcQ({ ...svcQ, [i]: q })
  }
  React.useEffect(()=>{
    const timers: number[] = []
    Object.entries(svcQ).forEach(([k,q])=>{
      const idx = Number(k)
      const t = window.setTimeout(async ()=>{
        if (!q) { setSvcOpts(prev=> ({ ...prev, [idx]: [] })); return }
        const { items } = await listServices(q,1,10)
        setSvcOpts(prev=> ({ ...prev, [idx]: items as any }))
      },300) as unknown as number
      timers.push(t)
    })
    return ()=> timers.forEach(t=> window.clearTimeout(t))
  }, [svcQ])
  const pickService = async (i:number, s: Service)=>{
    // set default from catalog
    setLine(i, { description: s.name, price: Number(s.price||0), sale_type:'service', code: s.code||'' })
    setSvcOpts(prev=> ({ ...prev, [i]: [] }))
    // try client-specific price
    try{
      const clientId = (hdr.client||'').trim()
      if (clientId && (s.code||'').trim()){
        const today = (hdr.date||'').trim()
        const { unit_price } = await resolveClientUnitPrice(clientId, { sale_type: 'service', code: s.code!, qty: lines[i]?.qty||1, date: today||undefined })
        if (unit_price!=null){
          setLine(i, { price: Number(unit_price) })
        }
      }
    } catch{}
  }

  // When qty or client/date changes, re-evaluate client pricing per line that has a code
  React.useEffect(()=>{
    const doResolve = async ()=>{
      const clientId = (hdr.client||'').trim()
      if (!clientId) return
      const dt = (hdr.date||'').trim() || undefined
      const updated = await Promise.all(lines.map(async (ln)=>{
        if (!ln?.code) return ln
        try{
          const { unit_price } = await resolveClientUnitPrice(clientId, { sale_type: ln.sale_type||'service', code: ln.code!, qty: ln.qty||1, date: dt })
          if (unit_price!=null && Number(unit_price) !== Number(ln.price)) return { ...ln, price: Number(unit_price) }
        } catch{}
        return ln
      }))
      // Only set if something actually changed to avoid loops
      const changed = updated.some((u, idx)=> Number(u.price) !== Number(lines[idx].price))
      if (changed) setLines(updated)
    }
    doResolve()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hdr.client, hdr.date, JSON.stringify(lines.map(l=>({ code: l.code||'', qty: l.qty||0 })))])

  const submit = async (e: React.FormEvent)=>{
    e.preventDefault()
  if (!hdr.client) { alert((t('client') as string) + ' ' + (t('required') as string || 'required')); return }
  await createOrder({ ...hdr, lines, series: seriesId || undefined });
  setHdr({ number:'', date:'', client:'', client_name:'', currency:'EUR', notes:'', discount_rate: 0, discount_amount: 0, tax_rate: 0 }); setLines([{ description:'', qty:1, price:0 }]); reload()
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold mb-4">{t('sales_orders') || 'Sales Orders'}</h1>
      
      {/* Create Form */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <form onSubmit={submit} className="space-y-4">
        {/* Header box */}
        <div className="border border-gray-300 dark:border-gray-600 rounded-lg p-4 space-y-3 bg-gray-50 dark:bg-gray-800/50">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div className="text-xs text-gray-500">{t('number')||'Number'}: <span className="font-medium">{hdr.number ? hdr.number : (t('auto')||'auto')}</span></div>
            <input type="date" value={hdr.date} onChange={e=>setHdr({...hdr, date:e.target.value})} className="input" />
          <div className="relative">
            <input placeholder={t('client')||'Client'} value={hdr.client_name} onChange={e=>{ setHdr({...hdr, client_name:e.target.value}); setClientQ(e.target.value) }} className="input w-full" />
            {clientOpts.length>0 && (
              <div className="absolute z-10 bg-white dark:bg-gray-900 border w-full max-h-56 overflow-auto">
                {clientOpts.map((c:any)=> {
                  const full = (c.first_name || c.last_name) ? `${c.first_name||''} ${c.last_name||''}`.trim() : (c.name||'')
                  return (
                    <div key={c.id as string} className="px-2 py-1 hover:bg-gray-100 cursor-pointer flex items-center justify-between" onClick={()=>pickClient(c)}>
                      <div className="truncate">
                        <div className="font-medium truncate">{c.code? `${c.code} - ${full}` : full}</div>
                        <div className="text-xs text-gray-500 truncate">{[c.tax_id, c.email, c.phone].filter(Boolean).join(' · ')}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
            <input placeholder={t('currency')||'Currency'} value={hdr.currency} onChange={e=>setHdr({...hdr, currency:e.target.value})} className="input" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <select value={seriesId} onChange={(e)=>setSeriesId(e.target.value)} className="input">
              <option value="">{t('series') || 'Series'}</option>
              {series.map((s:any)=> (<option key={s.id} value={s.id}>{s.prefix}{String(s.next_number).padStart(s.padding, '0')}</option>))}
            </select>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500 w-20">{t('discount')||'Discount'} %</label>
              <input type="number" step="0.01" value={(hdr as any).discount_rate||0} onChange={e=>setHdr({...hdr, discount_rate: Number(e.target.value)||0})} className="input" />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500 w-20">{t('discount')||'Discount'} {hdr.currency||''}</label>
              <input type="number" step="0.01" value={(hdr as any).discount_amount||0} onChange={e=>setHdr({...hdr, discount_amount: Number(e.target.value)||0})} className="input" />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500 w-20">IVA %</label>
              <input type="number" step="0.01" value={(hdr as any).tax_rate||0} onChange={e=>setHdr({...hdr, tax_rate: Number(e.target.value)||0})} className="input" />
            </div>
          </div>
          <textarea placeholder={t('description')||'Notes'} value={(hdr as any).notes} onChange={e=>setHdr({...hdr, notes:e.target.value})} className="input w-full" rows={2} />
          {hdr.client && (<div className="text-xs text-gray-500">{t('client')}: {hdr.client_name}</div>)}
        </div>
        <div>
          <table className="w-full text-sm">
            <thead><tr className="border-b"><th className="text-left py-1">{t('description')||'Description'}</th><th className="text-center py-1">{t('qty')||'Qty'}</th><th className="text-center py-1">{t('price')||'Price'}</th><th className="text-center py-1">{t('discount')||'Discount'} (% / {hdr.currency||''})</th><th className="text-center py-1">{t('total')||'Total'}</th></tr></thead>
            <tbody>
              {lines.map((ln, i)=> (
                <tr key={i} className="border-t">
                  <td className="relative">
                    <input placeholder={t('search_service')||t('services')||'Service'} value={ln.description} onChange={e=>{ setLine(i,{ description:e.target.value }); onSvcChange(i, e.target.value) }} className="input w-full" />
                    {(svcOpts[i]?.length||0) > 0 && (
                      <div className="absolute z-10 bg-white dark:bg-gray-900 border w-full max-h-48 overflow-auto">
                        {svcOpts[i]!.map((s:any)=> {
                          const title = s.code ? `${s.code} — ${s.name}` : s.name
                          const priceStr = s.price!=null ? `${Number(s.price).toFixed(2)} ${hdr.currency||''}` : ''
                          return (
                            <div key={s.id as string} className="px-2 py-1 hover:bg-gray-100 cursor-pointer flex items-center justify-between" onClick={()=>pickService(i, s)}>
                              <div className="truncate">{title}</div>
                              <div className="text-xs opacity-70 ml-2 whitespace-nowrap">{priceStr}</div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </td>
                  <td className="text-center"><input type="number" step="1" value={ln.qty} onChange={e=>setLine(i,{ qty:Number(e.target.value) })} className="input w-full" /></td>
                  <td className="text-center"><input type="number" step="0.01" value={ln.price} onChange={e=>setLine(i,{ price:Number(e.target.value) })} className="input w-full" /></td>
                  <td className="text-center flex gap-1">
                    <input type="number" step="0.01" placeholder="%" value={(ln as any).discount_rate||0} onChange={e=>setLine(i,{ ...(ln as any), discount_rate: Number(e.target.value)||0 })} className="input w-full" />
                    <input type="number" step="0.01" placeholder={t('discount') as string || 'Discount'} value={(ln as any).discount_amount||0} onChange={e=>setLine(i,{ ...(ln as any), discount_amount: Number(e.target.value)||0 })} className="input w-full" />
                  </td>
                  <td className="text-center">{calcNet(ln).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex justify-between mt-2">
            <button type="button" onClick={addLine} className="px-3 py-1 rounded border">+ {t('add_line')||'Add line'}</button>
            <TotalsSummary hdr={hdr} lines={lines} />
          </div>
        </div>
          <div className="flex items-center justify-end gap-4 border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
          <GrandTotal hdr={hdr} lines={lines} />
          <button className="btn btn-primary transition-all duration-200 hover:shadow-lg">{t('create')||'Create'}</button>
        </div>
      </form>
      </div>

      {/* List Table */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <h2 className="text-lg font-semibold mb-4">{t('list')||'List'}</h2>
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="px-4 py-3 font-semibold text-center">{t('number')||'Number'}</th>
            <th className="px-4 py-3 font-semibold text-center">{t('date')||'Date'}</th>
            <th className="px-4 py-3 font-semibold text-center">{t('total')||'Total'}</th>
            <th className="px-4 py-3 font-semibold"></th>
          </tr>
        </thead>
        <tbody>
        {items.map((o:any)=>(
          <tr key={o.id} className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-150">
            <td className="px-4 py-3 text-center">{o.number||''}</td>
            <td className="px-4 py-3 text-center">{o.date||''}</td>
            <td className="px-4 py-3 text-center">{o.total?.toFixed? o.total.toFixed(2): o.total ?? ''}</td>
            <td className="px-4 py-3 text-right"><div className="flex gap-2 justify-end flex-wrap">
              <button className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-200 text-sm font-medium" onClick={async()=>{ try{ const { order } = await (async()=>({ order: await getOrder(o.id) }))(); setEditing({ id:o.id }); setEditHdr({ number:order.number||'', date:order.date||'', currency:order.currency||'EUR', client:order.client||'', client_name:'', notes:(order as any).notes||'', discount_rate:(order as any).discount_rate||0, discount_amount:(order as any).discount_amount||0, tax_rate:(order as any).tax_rate||0 }); const linesAny = (order.lines as any)||[]; setEditLines(linesAny); const mm: Record<number,'rate'|'amount'> = {}; (linesAny||[]).forEach((ln:any, idx:number)=>{ mm[idx] = (ln?.discount_amount||0) > 0 ? 'amount' : 'rate' }); setEditDiscMode(mm); } catch(e:any){ alert(e?.message||'') } }}>{t('edit')||'Edit'}</button>
              <button className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-200 text-sm font-medium" onClick={()=> startConvert(o.id)}>{t('convert_to_invoice')||'To Invoice'}</button>
              <button className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-200 text-sm font-medium" onClick={async()=>{
                // fetch PDF with auth and save
                try {
                  const res = await fetch(`${orderPdfUrl(o.id)}`, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')||''}`, 'Accept-Language': i18n.language || 'en' } })
                  if (!res.ok) {
                    let msg = `${res.status}`;
                    try { const j = await res.json(); if (j?.error) msg = j.error } catch {}
                    alert(`${t('save_pdf')||'Save PDF'}: ${msg}`);
                    return
                  }
                  const blob = await res.blob();
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a'); a.href = url; a.download = `order_${o.number||o.id}.pdf`; a.click(); URL.revokeObjectURL(url);
                } catch (e:any) { alert(`${t('save_pdf')||'Save PDF'}: ${e?.message||''}`) }
              }}>{t('save_pdf')||'Save PDF'}</button>
              <button className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-200 text-sm font-medium" onClick={async()=>{
                try {
                  const res = await fetch(`${orderPdfUrl(o.id)}`, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')||''}`, 'Accept-Language': i18n.language || 'en' } })
                  if (!res.ok) {
                    let msg = `${res.status}`; try { const j = await res.json(); if (j?.error) msg = j.error } catch {}
                    alert(`${t('print')||'Print'}: ${msg}`); return
                  }
                  const blob = await res.blob();
                  const url = URL.createObjectURL(blob);
                  const w = window.open(url, '_blank'); if (w) { setTimeout(()=>{ try { w.focus(); w.print(); } catch {} }, 500) }
                } catch (e:any) { alert(`${t('print')||'Print'}: ${e?.message||''}`) }
              }}>{t('print')||'Print'}</button>
              <button className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-200 text-sm font-medium" onClick={async()=>{
                // open email modal prefilled with client email if available
                try {
                  const ord = await getOrder(o.id)
                  let suggested = ''
                  if (ord?.client) {
                    try { const cli = await getClient(ord.client as string); suggested = (cli as any)?.email || '' } catch {}
                  }
                  const defaultMessage = `${t('Bem-vindo')||'Olá'},\n\n${t('sales_orders')||'Encomenda'} ${o.number||o.id} - ${o.date||''}.` 
                  setEmailing({ id:o.id, to:'', cc:'', bcc:'', suggestedTo: suggested, defaultMessage })
                } catch (e:any) { alert(e?.message||'') }
              }}>{t('email')||'Email'}</button>
            </div></td>
          </tr>
        ))}
      </tbody></table>
      </div>
      </div>
      
      {/* Email modal */}
  <EmailModal
    onSend={async (payload) => {
      if (!emailing) return;
      try {
        const r: any = await sendOrderEmail(emailing.id, payload);
        if (r?.ok) {
          alert(t('smtp_ok') as string);
        } else if (r?.error) {
          alert(`${t('smtp_error')}: ${r.error}`);
        } else {
          alert(t('smtp_ok') as string);
        }
        setEmailing(null);
      } catch (e: any) {
        const isTimeout = e?.code === 'ECONNABORTED' || /timeout/i.test(e?.message || '');
        if (isTimeout) {
          try {
            const r2: any = await sendOrderEmail(emailing.id, payload);
            if (r2?.ok) {
              alert(t('smtp_ok') as string);
            } else if (r2?.error) {
              alert(`${t('smtp_error')}: ${r2.error}`);
            } else {
              alert(t('smtp_ok') as string);
            }
            setEmailing(null);
            return;
          } catch (e2: any) {
            const msg2 = e2?.response?.data?.error || e2?.message || '';
            alert(`${t('smtp_error')}: ${msg2}`);
          }
        } else {
          const msg = e?.response?.data?.error || e?.message || '';
          alert(`${t('smtp_error')}: ${msg}`);
        }
      }
    }}
    emailing={emailing}
    onClose={() => setEmailing(null)}
  />
  {/* Edit modal */}
  {editing && (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t('edit')||'Edit'}</h3>
          <button onClick={()=>setEditing(null)} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors">✕</button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
          <input placeholder={t('number')||'Number'} value={editHdr.number||''} readOnly className="input bg-gray-100 dark:bg-gray-800 cursor-not-allowed" />
          <input type="date" value={editHdr.date||''} onChange={e=>setEditHdr({...editHdr, date:e.target.value})} className="input" />
          <div className="relative col-span-2">
            <input placeholder={t('client')||'Client'} value={editHdr.client_name||''} onChange={e=>{ setEditHdr({...editHdr, client_name:e.target.value}); setEditClientQ(e.target.value) }} className="input w-full" />
            {editClientOpts.length>0 && (
              <div className="absolute z-10 bg-white dark:bg-gray-900 border w-full max-h-56 overflow-auto">
                {editClientOpts.map((c:any)=>{ const full=c.name; return (<div key={c.id} className="px-2 py-1 hover:bg-gray-100 cursor-pointer" onClick={()=>pickEditClient(c)}>{c.code? `${c.code} - ${full}`: full}</div>) })}
              </div>
            )}
          </div>
          <input placeholder={t('currency')||'Currency'} value={editHdr.currency||''} onChange={e=>setEditHdr({...editHdr, currency:e.target.value})} className="input" />
          <input placeholder={`${t('discount')||'Discount'} %`} type="number" step="0.01" value={editHdr.discount_rate||0} onChange={e=>setEditHdr({...editHdr, discount_rate: Number(e.target.value)||0})} className="input" />
          <input placeholder={`${t('discount')||'Discount'} ${editHdr.currency||''}`} type="number" step="0.01" value={editHdr.discount_amount||0} onChange={e=>setEditHdr({...editHdr, discount_amount: Number(e.target.value)||0})} className="input" />
          <input placeholder={`Tax %`} type="number" step="0.01" value={editHdr.tax_rate||0} onChange={e=>setEditHdr({...editHdr, tax_rate: Number(e.target.value)||0})} className="input" />
          <input placeholder={t('description')||'Notes'} value={editHdr.notes||''} onChange={e=>setEditHdr({...editHdr, notes:e.target.value})} className="input col-span-2" />
        </div>
        <table className="w-full text-sm mb-3">
          <thead><tr><th>{t('description')||'Description'}</th><th>{t('qty')||'Qty'}</th><th>{t('price')||'Price'}</th><th>{t('discount')||'Discount'}</th><th></th></tr></thead>
          <tbody>
            {editLines.map((ln:any,i:number)=> (
              <tr key={i} className="border-t">
                <td><input placeholder={t('description')||'Description'} value={ln.description||''} onChange={e=>setEditLines(editLines.map((x,idx)=> idx===i? {...x, description:e.target.value}: x))} className="input w-full" /></td>
                <td className="text-center"><input placeholder={t('qty')||'Qty'} type="number" step="1" value={ln.qty||0} onChange={e=>setEditLines(editLines.map((x,idx)=> idx===i? {...x, qty:Number(e.target.value)}: x))} className="input w-full" /></td>
                <td className="text-center"><input placeholder={t('price')||'Price'} type="number" step="0.01" value={ln.price||0} onChange={e=>setEditLines(editLines.map((x,idx)=> idx===i? {...x, price:Number(e.target.value)}: x))} className="input w-full" /></td>
                <td className="text-center">
                  <div className="flex items-center gap-2 mb-1 justify-center">
                    <label className="text-xs flex items-center gap-1"><input type="radio" checked={(editDiscMode[i]||'rate')==='rate'} onChange={()=>setEditDiscMode(prev=>({...prev, [i]:'rate'}))} />%</label>
                    <label className="text-xs flex items-center gap-1"><input type="radio" checked={(editDiscMode[i]||'rate')==='amount'} onChange={()=>setEditDiscMode(prev=>({...prev, [i]:'amount'}))} />{editHdr.currency||''}</label>
                  </div>
                  {(editDiscMode[i]||'rate')==='rate' ? (
                    <input placeholder="%" type="number" step="0.01" value={ln.discount_rate||0} onChange={e=>setEditLines(editLines.map((x,idx)=> idx===i? {...x, discount_rate:Number(e.target.value), discount_amount:0}: x))} className="input w-full" />
                  ) : (
                    <input placeholder={t('discount') as string || 'Discount'} type="number" step="0.01" value={ln.discount_amount||0} onChange={e=>setEditLines(editLines.map((x,idx)=> idx===i? {...x, discount_amount:Number(e.target.value), discount_rate:0}: x))} className="input w-full" />
                  )}
                </td>
                <td className="text-right"><button className="px-2 py-1 rounded border" onClick={()=>setEditLines(editLines.filter((_,idx)=> idx!==i))}>{t('remove')||'Remove'}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mb-3"><button className="px-3 py-1 rounded border" onClick={()=>setEditLines([...editLines, { description:'', qty:1, price:0 }])}>+ {t('add_line')||'Add line'}</button></div>
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-200 font-medium" onClick={()=>setEditing(null)}>{t('cancel') as string}</button>
          <button className="px-4 py-2 rounded-lg bg-gray-900 text-white dark:bg-gray-700 hover:shadow-lg transition-all duration-200 font-medium" onClick={async()=>{ try{ await updateOrder(editing.id, { ...editHdr, lines: editLines }); setEditing(null); reload() } catch(e:any){ alert(e?.message||'') } }}>{t('save') as string}</button>
        </div>
      </div>
    </div>
  )}
  {/* Convert dialog */}
  {convertDlg.open && (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t('convert_to_invoice')||'Convert to Invoice'}</h3>
          <button onClick={()=>setConvertDlg({ open:false })} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors">✕</button>
        </div>
        <div className="space-y-2">
          <label className="text-sm">{t('choose_series')||'Choose series'}</label>
          <select value={convertDlg.seriesId||''} onChange={(e)=>setConvertDlg(prev=> ({ ...prev, seriesId: e.target.value }))} className="input w-full">
            <option value="">{t('series') || 'Series'}</option>
            {series.filter((s:any)=> s.doc_type==='invoice').map((s:any)=> (
              <option key={s.id} value={s.id}>{s.prefix}{String(s.next_number).padStart(s.padding, '0')}</option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-200 font-medium" onClick={()=>setConvertDlg({ open:false })}>{t('cancel')||'Cancel'}</button>
          <button className="px-4 py-2 rounded-lg bg-gray-900 text-white dark:bg-gray-700 hover:shadow-lg transition-all duration-200 font-medium" onClick={doConvert}>{t('convert_to_invoice')||'Convert'}</button>
        </div>
      </div>
    </div>
  )}
    </div>
  )
}

// local EmailModal removed in favor of shared component
