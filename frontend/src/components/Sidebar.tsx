import React from 'react'
import { Link } from 'react-router-dom'

export default function Sidebar(){
  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 overflow-y-auto border-r bg-white dark:bg-gray-900 dark:border-gray-800">
      <Link to="/" className="p-4 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
        <img src="/assets/logos/vivae-erp-logo-main.svg" alt="VIVAE ERP" className="h-8 w-auto" />
        <span className="text-xl font-bold">VIVAE ERP</span>
      </Link>
    </aside>
  )
}
