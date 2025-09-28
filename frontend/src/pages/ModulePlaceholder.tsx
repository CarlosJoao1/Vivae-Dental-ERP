import React from 'react'
import DashboardLayout from '@/layouts/DashboardLayout'
import { useParams } from 'react-router-dom'

export default function ModulePlaceholder(){
  const { module } = useParams()
  return (
    <DashboardLayout>
      <h1 className="text-2xl font-bold mb-4">Módulo: {module}</h1>
      <p className="text-gray-600 dark:text-gray-300">Conteúdo em desenvolvimento.</p>
    </DashboardLayout>
  )
}
