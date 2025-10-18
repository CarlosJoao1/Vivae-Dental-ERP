import React from 'react'
import { useTranslation } from 'react-i18next'

export default function WorkCenters(){
  const { t } = useTranslation()
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold mb-4">{t('work_centers') || 'Centros de Trabalho'}</h1>
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-start gap-4">
          <div className="text-5xl">🔒</div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{t('unlicensed') || 'Módulo Não Licenciado'}</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('work_centers_message') || 'Este módulo requer licenciamento adicional. Entre em contato com o administrador do sistema.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
