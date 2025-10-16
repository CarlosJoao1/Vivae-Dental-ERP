import React from 'react'
import { useTranslation } from 'react-i18next'
import ModulePlaceholder from '@/pages/ModulePlaceholder'

export default function CRM(){
  const { t } = useTranslation()
  return (
    <ModulePlaceholder
      title={t('crm') as string}
      description={t('crm_unlicensed') as string}
    >
      <div className="mt-4 rounded border p-3 bg-amber-50 text-amber-800 text-sm">
        {t('crm_work_in_progress')}
      </div>
    </ModulePlaceholder>
  )
}
