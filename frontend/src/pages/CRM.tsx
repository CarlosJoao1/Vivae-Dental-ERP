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
      <div className="mt-6 rounded-xl border border-amber-200 dark:border-amber-800 p-6 bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 text-amber-900 dark:text-amber-200 shadow-md hover:shadow-lg transition-all duration-300">
        <div className="flex items-start gap-4">
          <div className="text-4xl">🚧</div>
          <div>
            <div className="font-semibold text-lg mb-2">{t('work_in_progress') || 'Work in Progress'}</div>
            <div className="text-sm opacity-90">{t('crm_work_in_progress')}</div>
          </div>
        </div>
      </div>
    </ModulePlaceholder>
  )
}
