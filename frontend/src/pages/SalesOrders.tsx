import React from 'react'
import i18n from '@/i18n'
import { listOrders, createOrder, type Line, orderPdfUrl, sendOrderEmail, getOrder, updateOrder } from '@/api/sales'
import { searchClientsBrief, type Client, listServices, type Service, getClient, listSeries } from '@/api/masterdata'
import { useTranslation } from 'react-i18next'

export default function SalesOrders(){
  const { t } = useTranslation()
  const [items, setItems] = React.useState<any[]>([])
  const [hdr, setHdr] = React.useState({ number:'', date:'', client:'', client_name:'', currency:'EUR', notes:'', discount_rate: 0, discount_amount: 0, tax_rate: 0 })
  const [clientOpts, setClientOpts] = React.useState<Client[]>([])
  const [clientQ, setClientQ] = React.useState('')
  const [lines, setLines] = React.useState<Line[]>([{ description:'', qty:1, price:0 }])
  const [series, setSeries] = React.useState<any[]>([])
  const [seriesId, setSeriesId] = React.useState<string>('')
  const [emailing, setEmailing] = React.useState<{ id:string; to:string; cc:string; bcc:string; suggestedTo?:string; defaultMessage?: string } | null>(null)
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

  const addLine = ()=> setLines([...lines, { description:'', qty:1, price:0 }])
  const setLine = (i:number, patch: Partial<Line>)=> setLines(lines.map((ln,idx)=> idx===i ? { ...ln, ...patch } : ln ))
  const sumGross = lines.reduce((s,ln)=> (s + (ln.qty||0)*(ln.price||0)), 0)
  const sumAfterLine = lines.reduce((s,ln)=> {
    const qty = ln.qty||0; const price = ln.price||0
    const gross = qty*price
    const dr = Number((ln as any).discount_rate||0)
    const da = Number((ln as any).discount_amount||0)
    const disc = (da||0) ? (da||0) : (dr ? gross*(dr/100) : 0)
    return s + Math.max(0, gross - disc)
  }, 0)
  const globalDisc = (hdr.discount_rate && hdr.discount_rate>0) ? (sumAfterLine * (hdr.discount_rate/100)) : (hdr as any).discount_amount || 0
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
  const pickService = (i:number, s: Service)=>{
    setLine(i, { description: s.name, price: Number(s.price||0) })
    setSvcOpts(prev=> ({ ...prev, [i]: [] }))
  }

  const submit = async (e: React.FormEvent)=>{
    e.preventDefault()
  if (!hdr.client) { alert((t('client') as string) + ' ' + (t('required') as string || 'required')); return }
  await createOrder({ ...hdr, lines, series: seriesId || undefined });
  setHdr({ number:'', date:'', client:'', client_name:'', currency:'EUR', notes:'', discount_rate: 0, discount_amount: 0, tax_rate: 0 }); setLines([{ description:'', qty:1, price:0 }]); reload()
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">{t('sales_orders') || 'Sales Orders'}</h1>
      <form onSubmit={submit} className="space-y-3 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <input placeholder={t('number')||'Number'} value={hdr.number} onChange={e=>setHdr({...hdr, number:e.target.value})} className="input" />
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
          <input type="number" step="0.01" placeholder={`${t('discount')||'Discount'} %`} value={(hdr as any).discount_rate||0} onChange={e=>setHdr({...hdr, discount_rate: Number(e.target.value)||0})} className="input" />
          <input type="number" step="0.01" placeholder={`${t('discount')||'Discount'} ${hdr.currency||''}`} value={(hdr as any).discount_amount||0} onChange={e=>setHdr({...hdr, discount_amount: Number(e.target.value)||0})} className="input" />
          <input type="number" step="0.01" placeholder={`Tax %`} value={(hdr as any).tax_rate||0} onChange={e=>setHdr({...hdr, tax_rate: Number(e.target.value)||0})} className="input" />
        </div>
        <textarea placeholder={t('description')||'Notes'} value={(hdr as any).notes} onChange={e=>setHdr({...hdr, notes:e.target.value})} className="input w-full" rows={2} />
        {hdr.client && (<div className="text-xs text-gray-500">{t('client')}: {hdr.client_name}</div>)}
        <div>
          <table className="w-full text-sm">
            <thead><tr><th>{t('description')||'Description'}</th><th>{t('qty')||'Qty'}</th><th>{t('price')||'Price'}</th><th>{t('discount')||'Discount'}</th><th>{t('total')||'Total'}</th></tr></thead>
            <tbody>
              {lines.map((ln, i)=> (
                <tr key={i} className="border-t">
                  <td className="relative">
                    <input value={ln.description} onChange={e=>{ setLine(i,{ description:e.target.value }); onSvcChange(i, e.target.value) }} className="input w-full" />
                    {(svcOpts[i]?.length||0) > 0 && (
                      <div className="absolute z-10 bg-white dark:bg-gray-900 border w-full max-h-48 overflow-auto">
                        {svcOpts[i]!.map((s:any)=> (
                          <div key={s.id as string} className="px-2 py-1 hover:bg-gray-100 cursor-pointer" onClick={()=>pickService(i, s)}>
                            {s.name} {s.price!=null? `- ${s.price}`:''}
                          </div>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="text-center"><input type="number" step="1" value={ln.qty} onChange={e=>setLine(i,{ qty:Number(e.target.value) })} className="input w-full" /></td>
                  <td className="text-center"><input type="number" step="0.01" value={ln.price} onChange={e=>setLine(i,{ price:Number(e.target.value) })} className="input w-full" /></td>
                  <td className="text-center flex gap-1">
                    <input type="number" step="0.01" placeholder="%" value={(ln as any).discount_rate||0} onChange={e=>setLine(i,{ ...(ln as any), discount_rate: Number(e.target.value)||0 })} className="input w-full" />
                    <input type="number" step="0.01" placeholder={t('discount') as string || 'Discount'} value={(ln as any).discount_amount||0} onChange={e=>setLine(i,{ ...(ln as any), discount_amount: Number(e.target.value)||0 })} className="input w-full" />
                  </td>
                  <td className="text-center">{(()=>{ const qty=ln.qty||0, price=ln.price||0; const gross=qty*price; const dr=Number((ln as any).discount_rate||0); const da=Number((ln as any).discount_amount||0); const disc = (da||0)? (da||0) : (dr? gross*(dr/100):0); return (Math.max(0,gross-disc)).toFixed(2) })()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex justify-between mt-2">
            <button type="button" onClick={addLine} className="px-3 py-1 rounded border">+ {t('add_line')||'Add line'}</button>
            <div className="text-right space-y-1">
              <div>{t('subtotal')||'Subtotal'}: {sumGross.toFixed(2)} {hdr.currency}</div>
              <div>{t('line_discount')||'Line discount'}: {(sumGross - sumAfterLine).toFixed(2)} {hdr.currency}</div>
              <div>{t('subtotal_after_discount')||'Subtotal'}: {sumAfterLine.toFixed(2)} {hdr.currency}</div>
              {(hdr.discount_rate||0) > 0 || (hdr as any).discount_amount ? (<div>{t('global_discount')||'Global discount'}: {globalDisc.toFixed(2)} {hdr.currency}</div>) : null}
              <div>{t('tax')||'Tax'}: {taxAmount.toFixed(2)} {hdr.currency}</div>
              <div className="font-semibold">{t('grand_total')||'Total'}: {grandTotal.toFixed(2)} {hdr.currency}</div>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-end gap-4">
          <div className="text-lg font-semibold">{t('grand_total')||'Total'}: {grandTotal.toFixed(2)} {hdr.currency}</div>
          <button className="btn btn-primary">{t('create')||'Create'}</button>
        </div>
      </form>

      <h2 className="text-lg font-semibold mb-2">{t('list')||'List'}</h2>
      <table className="w-full text-sm"><thead><tr><th>{t('number')||'Number'}</th><th>{t('date')||'Date'}</th><th>{t('total')||'Total'}</th><th></th></tr></thead><tbody>
        {items.map((o:any)=>(
          <tr key={o.id} className="border-t">
            <td className="text-center">{o.number||''}</td>
            <td className="text-center">{o.date||''}</td>
            <td className="text-center">{o.total?.toFixed? o.total.toFixed(2): o.total ?? ''}</td>
            <td className="text-right flex gap-2 justify-end px-2 py-1">
              <button className="px-2 py-1 rounded border" onClick={async()=>{ try{ const { order } = await (async()=>({ order: await getOrder(o.id) }))(); setEditing({ id:o.id }); setEditHdr({ number:order.number||'', date:order.date||'', currency:order.currency||'EUR', client:order.client||'', client_name:'', notes:(order as any).notes||'', discount_rate:(order as any).discount_rate||0, discount_amount:(order as any).discount_amount||0, tax_rate:(order as any).tax_rate||0 }); const linesAny = (order.lines as any)||[]; setEditLines(linesAny); const mm: Record<number,'rate'|'amount'> = {}; (linesAny||[]).forEach((ln:any, idx:number)=>{ mm[idx] = (ln?.discount_amount||0) > 0 ? 'amount' : 'rate' }); setEditDiscMode(mm); } catch(e:any){ alert(e?.message||'') } }}>{t('edit')||'Edit'}</button>
              <button className="px-2 py-1 rounded border" onClick={async()=>{
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
              <button className="px-2 py-1 rounded border" onClick={async()=>{
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
              <button className="px-2 py-1 rounded border" onClick={async()=>{
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
            </td>
          </tr>
        ))}
      </tbody></table>
      {/* Email modal */}
  <EmailModal onSend={async (payload)=>{ if (emailing) { try { const r:any = await sendOrderEmail(emailing.id, payload); if (r?.ok){ alert(t('smtp_ok') as string) } else if (r?.error){ alert(`${t('smtp_error')}: ${r.error}`) } else { alert(t('smtp_ok') as string) } setEmailing(null) } catch(e:any){ const msg = e?.response?.data?.error || e?.message || ''; alert(`${t('smtp_error')}: ${msg}`) } } }} emailing={emailing} onClose={()=>setEmailing(null)} />
  {/* Edit modal */}
  {editing && (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-3xl p-4">
        <div className="flex items-center justify-between mb-3"><h3 className="text-lg font-semibold">{t('edit')||'Edit'}</h3><button onClick={()=>setEditing(null)}>✕</button></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
          <input placeholder={t('number')||'Number'} value={editHdr.number||''} onChange={e=>setEditHdr({...editHdr, number:e.target.value})} className="input" />
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
        <div className="flex justify-end gap-2">
          <button className="px-3 py-1 rounded border" onClick={()=>setEditing(null)}>{t('cancel') as string}</button>
          <button className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700" onClick={async()=>{ try{ await updateOrder(editing.id, { ...editHdr, lines: editLines }); setEditing(null); reload() } catch(e:any){ alert(e?.message||'') } }}>{t('save') as string}</button>
        </div>
      </div>
    </div>
  )}
    </div>
  )
}

function EmailModal({ emailing, onSend, onClose }:{ emailing: { id:string; to:string; cc:string; bcc:string; suggestedTo?:string; defaultMessage?: string } | null, onSend:(p:{to?:string;cc?:string;bcc?:string;message?:string})=>Promise<void>, onClose:()=>void }){
  const { t } = useTranslation()
  const [to,setTo]=React.useState(emailing?.suggestedTo||'')
  const [cc,setCc]=React.useState('')
  const [bcc,setBcc]=React.useState('')
  const [message,setMessage]=React.useState(emailing?.defaultMessage||'')
  React.useEffect(()=>{ setTo(emailing?.suggestedTo||''); setCc(''); setBcc(''); setMessage(emailing?.defaultMessage||'') },[emailing])
  if (!emailing) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-xl p-4">
        <div className="flex items-center justify-between mb-3"><h3 className="text-lg font-semibold">{t('email')||'Email'}</h3><button onClick={onClose}>✕</button></div>
        <div className="space-y-2">
          <input placeholder={`${t('to')||'To'} (a;b;c)`} value={to} onChange={e=>setTo(e.target.value)} className="input w-full" />
          <input placeholder={`${t('cc')||'Cc'} (a;b;c)`} value={cc} onChange={e=>setCc(e.target.value)} className="input w-full" />
          <input placeholder={`${t('bcc')||'Bcc'} (a;b;c)`} value={bcc} onChange={e=>setBcc(e.target.value)} className="input w-full" />
          <div className="text-xs text-gray-500">{t('emails_semicolon')||'Separe múltiplos emails com ;'}</div>
          <textarea placeholder={t('description')||'Message'} value={message} onChange={e=>setMessage(e.target.value)} className="input w-full" rows={3} />
          <div className="flex justify-end gap-2"><button onClick={onClose} className="px-3 py-1 rounded border">{t('cancel') as string}</button><button onClick={()=>onSend({ to, cc, bcc, message })} className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('send')||'Send'}</button></div>
        </div>
      </div>
    </div>
  )
}
