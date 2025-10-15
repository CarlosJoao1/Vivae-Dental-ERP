import React from 'react'
import i18n from '@/i18n'
import { listInvoices, createInvoice, type Line, invoicePdfUrl, getInvoice, sendInvoiceEmail } from '@/api/sales'
import { listClients, type Client, listServices, type Service, getClient, listSeries } from '@/api/masterdata'
import { useTranslation } from 'react-i18next'

export default function SalesInvoices(){
  const { t } = useTranslation()
  const [items, setItems] = React.useState<any[]>([])
  const [hdr, setHdr] = React.useState({ number:'', date:'', client:'', client_name:'', currency:'EUR', status:'draft' })
  const [lines, setLines] = React.useState<Line[]>([{ description:'', qty:1, price:0 }])
  const [series, setSeries] = React.useState<any[]>([])
  const [seriesId, setSeriesId] = React.useState<string>('')
  const [emailing, setEmailing] = React.useState<{ id:string; to:string; cc:string; bcc:string; suggestedTo?:string } | null>(null)
  const [clientOpts, setClientOpts] = React.useState<Client[]>([])
  const [clientQ, setClientQ] = React.useState('')

  const reload = async ()=>{ const { items } = await listInvoices(); setItems(items) }
  React.useEffect(()=>{ reload(); (async ()=>{ const { items } = await listSeries(); setSeries(items as any) })() }, [])

  const addLine = ()=> setLines([...lines, { description:'', qty:1, price:0 }])
  const setLine = (i:number, patch: Partial<Line>)=> setLines(lines.map((ln,idx)=> idx===i ? { ...ln, ...patch } : ln ))
  const total = lines.reduce((s,ln)=> s + (ln.qty||0)*(ln.price||0), 0)
  React.useEffect(()=>{
    const h = setTimeout(async ()=>{
      if (!clientQ) { setClientOpts([]); return }
      const { items } = await listClients(clientQ, 1, 10)
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
  const [svcQ, setSvcQ] = React.useState<Record<number, string>>({})
  const [svcOpts, setSvcOpts] = React.useState<Record<number, Service[]>>({})
  const onSvcChange = (i:number, q:string)=>{ setSvcQ({ ...svcQ, [i]: q }) }
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
  await createInvoice({ ...hdr, lines, series: seriesId || undefined });
  setHdr({ number:'', date:'', client:'', client_name:'', currency:'EUR', status:'draft' }); setLines([{ description:'', qty:1, price:0 }]); reload()
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">{t('sales_invoices') || 'Sales Invoices'}</h1>
      <form onSubmit={submit} className="space-y-3 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <input placeholder={t('number')||'Number'} value={hdr.number} onChange={e=>setHdr({...hdr, number:e.target.value})} className="input" />
          <input type="date" value={hdr.date} onChange={e=>setHdr({...hdr, date:e.target.value})} className="input" />
          <div className="relative">
            <input placeholder={t('client')||'Client'} value={hdr.client_name} onChange={e=>{ setHdr({...hdr, client_name:e.target.value}); setClientQ(e.target.value) }} className="input w-full" />
            {clientOpts.length>0 && (
              <div className="absolute z-10 bg-white dark:bg-gray-900 border w-full max-h-48 overflow-auto">
                {clientOpts.map(c=> (
                  <div key={c.id as string} className="px-2 py-1 hover:bg-gray-100 cursor-pointer" onClick={()=>pickClient(c)}>
                    {(c.first_name || c.last_name) ? `${c.first_name||''} ${c.last_name||''}`.trim() : c.name}
                  </div>
                ))}
              </div>
            )}
          </div>
          <input placeholder={t('currency')||'Currency'} value={hdr.currency} onChange={e=>setHdr({...hdr, currency:e.target.value})} className="input" />
          <select value={hdr.status} onChange={e=>setHdr({...hdr, status:e.target.value})} className="input">
            <option value="draft">Draft</option>
            <option value="issued">Issued</option>
            <option value="paid">Paid</option>
          </select>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <select value={seriesId} onChange={(e)=>setSeriesId(e.target.value)} className="input">
            <option value="">{t('series') || 'Series'}</option>
            {series.map((s:any)=> (<option key={s.id} value={s.id}>{s.prefix}{String(s.next_number).padStart(s.padding, '0')}</option>))}
          </select>
        </div>
        <div>
          <table className="w-full text-sm">
            <thead><tr><th>{t('description')||'Description'}</th><th>{t('qty')||'Qty'}</th><th>{t('price')||'Price'}</th><th>{t('total')||'Total'}</th></tr></thead>
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
                  <td className="text-center">{((ln.qty||0)*(ln.price||0)).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex justify-between mt-2">
            <button type="button" onClick={addLine} className="px-3 py-1 rounded border">+ {t('add_line')||'Add line'}</button>
            <div className="font-semibold">{t('total')||'Total'}: {total.toFixed(2)}</div>
          </div>
        </div>
        <div className="flex justify-end"><button className="btn btn-primary">{t('create')||'Create'}</button></div>
      </form>

      <h2 className="text-lg font-semibold mb-2">{t('list')||'List'}</h2>
      <table className="w-full text-sm"><thead><tr><th>{t('number')||'Number'}</th><th>{t('date')||'Date'}</th><th>{t('total')||'Total'}</th><th>{t('status')||'Status'}</th><th></th></tr></thead><tbody>
        {items.map((inv:any)=>(
          <tr key={inv.id} className="border-t">
            <td className="text-center">{inv.number||''}</td>
            <td className="text-center">{inv.date||''}</td>
            <td className="text-center">{inv.total?.toFixed? inv.total.toFixed(2): inv.total ?? ''}</td>
            <td className="text-center">{inv.status||''}</td>
            <td className="text-right flex gap-2 justify-end px-2 py-1">
              <button className="px-2 py-1 rounded border" onClick={async()=>{
                try {
                  const res = await fetch(`${invoicePdfUrl(inv.id)}`, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')||''}`, 'Accept-Language': i18n.language || 'en' } })
                  if (!res.ok) {
                    let msg = `${res.status}`; try { const j = await res.json(); if (j?.error) msg = j.error } catch {}
                    alert(`${t('save_pdf')||'Save PDF'}: ${msg}`); return
                  }
                  const blob = await res.blob();
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a'); a.href = url; a.download = `invoice_${inv.number||inv.id}.pdf`; a.click(); URL.revokeObjectURL(url);
                } catch (e:any) { alert(`${t('save_pdf')||'Save PDF'}: ${e?.message||''}`) }
              }}>{t('save_pdf')||'Save PDF'}</button>
              <button className="px-2 py-1 rounded border" onClick={async()=>{ try { const res = await fetch(`${invoicePdfUrl(inv.id)}`, { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')||''}`, 'Accept-Language': i18n.language || 'en' } }); if (!res.ok) { let msg = `${res.status}`; try { const j = await res.json(); if (j?.error) msg = j.error } catch {}; alert(`${t('print')||'Print'}: ${msg}`); return } const blob = await res.blob(); const url = URL.createObjectURL(blob); const w = window.open(url, '_blank'); if (w) { setTimeout(()=>{ try { w.focus(); w.print(); } catch {} }, 500) } } catch (e:any) { alert(`${t('print')||'Print'}: ${e?.message||''}`) } }}>{t('print')||'Print'}</button>
              <button className="px-2 py-1 rounded border" onClick={async()=>{
                try {
                  const iv = await getInvoice(inv.id)
                  let suggested = ''
                  if (iv?.client) {
                    try { const cli = await getClient(iv.client as string); suggested = (cli as any)?.email || '' } catch {}
                  }
                  setEmailing({ id:inv.id, to:'', cc:'', bcc:'', suggestedTo: suggested })
                } catch (e:any) { alert(e?.message||'') }
              }}>{t('email')||'Email'}</button>
            </td>
          </tr>
        ))}
      </tbody></table>
  <EmailModal onSend={async (payload)=>{ if (emailing) { try { const r:any = await sendInvoiceEmail(emailing.id, payload); if (r?.ok){ alert(t('smtp_ok') as string) } else if (r?.error){ alert(`${t('smtp_error')}: ${r.error}`) } else { alert(t('smtp_ok') as string) } setEmailing(null) } catch(e:any){ const msg = e?.response?.data?.error || e?.message || ''; alert(`${t('smtp_error')}: ${msg}`) } } }} emailing={emailing} onClose={()=>setEmailing(null)} />
    </div>
  )
}

function EmailModal({ emailing, onSend, onClose }:{ emailing: { id:string; to:string; cc:string; bcc:string; suggestedTo?:string } | null, onSend:(p:{to?:string;cc?:string;bcc?:string})=>Promise<void>, onClose:()=>void }){
  const { t } = useTranslation()
  const [to,setTo]=React.useState(emailing?.suggestedTo||'')
  const [cc,setCc]=React.useState('')
  const [bcc,setBcc]=React.useState('')
  React.useEffect(()=>{ setTo(emailing?.suggestedTo||''); setCc(''); setBcc('') },[emailing])
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
          <div className="flex justify-end gap-2"><button onClick={onClose} className="px-3 py-1 rounded border">{t('cancel') as string}</button><button onClick={()=>onSend({ to, cc, bcc })} className="px-3 py-1 rounded bg-gray-900 text-white dark:bg-gray-700">{t('send')||'Send'}</button></div>
        </div>
      </div>
    </div>
  )
}
