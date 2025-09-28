import React from 'react'
export default function ThemeToggle(){
  const [dark,setDark]=React.useState(document.documentElement.classList.contains('dark'))
  const toggle=()=>{
    const root=document.documentElement
    if(dark) root.classList.remove('dark'); else root.classList.add('dark')
    setDark(!dark); localStorage.setItem('theme',!dark?'dark':'light')
  }
  React.useEffect(()=>{ const s=localStorage.getItem('theme'); if(s==='dark'){document.documentElement.classList.add('dark'); setDark(true)} },[])
  return <button onClick={toggle} className="px-3 py-1 rounded border dark:border-gray-700">{dark?'🌙':'☀️'}</button>
}
