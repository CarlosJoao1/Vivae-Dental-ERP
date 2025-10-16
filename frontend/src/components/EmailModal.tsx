import React from 'react'
import { useTranslation } from 'react-i18next'

export type EmailingState = {
  id: string
  to: string
  cc: string
  bcc: string
  suggestedTo?: string
  defaultMessage?: string
} | null

export default function EmailModal({ emailing, onSend, onClose }:{
  emailing: EmailingState,
  onSend: (p:{to?:string;cc?:string;bcc?:string;message?:string})=>Promise<void>,
  onClose: ()=>void
}){
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
