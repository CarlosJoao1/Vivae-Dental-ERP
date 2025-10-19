import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export default function ProductionCosting() {
  const { t } = useTranslation()

  // Mock data
  const costData = {
    item_no: 'FG-CHAIR-001',
    standard_cost: 45.50,
    actual_cost: 48.20,
    variance: 2.70,
    breakdown: {
      material: { standard: 25.00, actual: 26.50, variance: 1.50 },
      labor: { standard: 15.00, actual: 16.20, variance: 1.20 },
      overhead: { standard: 5.50, actual: 5.50, variance: 0.00 }
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold">💰 {t('costing') || 'Custeio de Produção'}</h1>
        <p className="text-sm text-gray-600 mt-1">
          {t('costing_desc') || 'Análise de custos reais vs standard, variâncias'}
        </p>
      </div>

      {/* Cost Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('standard_cost') || 'Custo Standard'}</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            €{costData.standard_cost.toFixed(2)}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('actual_cost') || 'Custo Real'}</div>
          <div className="text-2xl font-bold text-orange-600 mt-1">
            €{costData.actual_cost.toFixed(2)}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('variance') || 'Variância'}</div>
          <div className={`text-2xl font-bold mt-1 ${costData.variance > 0 ? 'text-red-600' : 'text-green-600'}`}>
            {costData.variance > 0 ? '+' : ''}€{costData.variance.toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {((costData.variance / costData.standard_cost) * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold mb-4">📊 {t('cost_breakdown') || 'Decomposição de Custos'}</h2>
        
        <div className="space-y-4">
          {/* Material */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">📦 {t('material') || 'Material'}</span>
              <span className="text-sm text-gray-600">
                €{costData.breakdown.material.actual.toFixed(2)} / €{costData.breakdown.material.standard.toFixed(2)}
              </span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600"
                style={{ width: `${(costData.breakdown.material.actual / costData.actual_cost) * 100}%` }}
              />
            </div>
            <div className="mt-1 text-xs text-red-600">
              Variância: +€{costData.breakdown.material.variance.toFixed(2)}
            </div>
          </div>

          {/* Labor */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">👷 {t('labor') || 'Mão de Obra'}</span>
              <span className="text-sm text-gray-600">
                €{costData.breakdown.labor.actual.toFixed(2)} / €{costData.breakdown.labor.standard.toFixed(2)}
              </span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-600"
                style={{ width: `${(costData.breakdown.labor.actual / costData.actual_cost) * 100}%` }}
              />
            </div>
            <div className="mt-1 text-xs text-red-600">
              Variância: +€{costData.breakdown.labor.variance.toFixed(2)}
            </div>
          </div>

          {/* Overhead */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">🏭 {t('overhead') || 'Overhead'}</span>
              <span className="text-sm text-gray-600">
                €{costData.breakdown.overhead.actual.toFixed(2)} / €{costData.breakdown.overhead.standard.toFixed(2)}
              </span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-600"
                style={{ width: `${(costData.breakdown.overhead.actual / costData.actual_cost) * 100}%` }}
              />
            </div>
            <div className="mt-1 text-xs text-gray-600">
              Variância: €{costData.breakdown.overhead.variance.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Coming Soon */}
      <div className="card p-4">
        <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <p className="text-sm text-purple-800">
            🔮 <strong>{t('coming_soon') || 'Em breve'}:</strong> Cost reports por item, order, period. Variance analysis automática. Integration com Item Ledger Entries.
          </p>
        </div>
      </div>
    </div>
  )
}
