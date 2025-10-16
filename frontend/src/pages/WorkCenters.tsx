import React from 'react'
import { useTranslation } from 'react-i18next'

export default function WorkCenters(){
  const { t } = useTranslation()
  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-2">{t('work_centers') || 'Centros de Trabalho'}</h1>
      <div className="p-3 border rounded bg-yellow-50 text-yellow-800">{t('unlicensed') || 'Sem licenciamento para o utilizador.'}</div>
    </div>
  )
}
