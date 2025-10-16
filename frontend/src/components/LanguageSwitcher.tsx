import React from 'react'
import i18n from '@/i18n'

const langs = [{code:'pt',label:'PT'},{code:'en',label:'EN'},{code:'es',label:'ES'},{code:'fr',label:'FR'},{code:'cn',label:'CN'},{code:'de',label:'DE'}]

export default function LanguageSwitcher() {
  const [lng, setLng] = React.useState(i18n.language)
  const change = (c:string)=>{ i18n.changeLanguage(c); setLng(c) }
  return (
    <div className="flex gap-2">
      {langs.map(l=>(
        <button key={l.code} onClick={()=>change(l.code)} className={`px-2 py-1 rounded text-sm ${lng===l.code?'bg-gray-200 dark:bg-gray-700':'hover:bg-gray-100 dark:hover:bg-gray-800'}`}>{l.label}</button>
      ))}
    </div>
  )
}
