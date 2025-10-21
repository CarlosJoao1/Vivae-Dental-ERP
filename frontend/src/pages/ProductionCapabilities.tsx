import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../lib/api'
import WorkCenterForm from '@/components/production/WorkCenterForm'
import MachineCenterForm from '@/components/production/MachineCenterForm'

interface WorkCenter {
  id: string
  code: string
  name: string
  capacity: number
  efficiency_pct: number
  unit_cost: number
  overhead_rate: number
  blocked: boolean
  machine_centers_count?: number
}

interface MachineCenter {
  id: string
  code: string
  name: string
  work_center_code: string
  capacity: number
  efficiency_pct: number
  unit_cost: number
  blocked: boolean
}

export default function ProductionCapabilities() {
  const { t } = useTranslation()
  const [workCenters, setWorkCenters] = useState<WorkCenter[]>([])
  const [machineCenters, setMachineCenters] = useState<MachineCenter[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedWC, setSelectedWC] = useState<string | null>(null)
  const [showWCForm, setShowWCForm] = useState(false)
  const [showMCForm, setShowMCForm] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [wcRes, mcRes] = await Promise.all([
        api<any>('/api/production/work-centers'),
        api<any>('/api/production/machine-centers')
      ])
      setWorkCenters(Array.isArray(wcRes) ? wcRes : (wcRes?.items || []))
      setMachineCenters(Array.isArray(mcRes) ? mcRes : (mcRes?.items || []))
    } catch (error) {
      console.error('Failed to load capabilities:', error)
    } finally {
      setLoading(false)
    }
  }

  const getMachinesForWC = (wcCode: string) => {
    return machineCenters.filter(mc => mc.work_center_code === wcCode)
  }

  const getEfficiencyColor = (eff: number) => {
    if (eff >= 90) return 'text-green-600'
    if (eff >= 75) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getTotalCapacity = () => {
    return workCenters.reduce((sum, wc) => sum + (wc.blocked ? 0 : wc.capacity), 0)
  }

  const getAvgEfficiency = () => {
    const active = workCenters.filter(wc => !wc.blocked)
    if (active.length === 0) return 0
    return active.reduce((sum, wc) => sum + wc.efficiency_pct, 0) / active.length
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">⚡ {t('capabilities') || 'Capacidades de Produção'}</h1>
          <p className="text-sm text-gray-600 mt-1">
            {t('capabilities_desc') || 'Gestão de Work Centers e Machine Centers'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowWCForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            + {t('new_work_center') || 'Novo Work Center'}
          </button>
          <button
            onClick={() => setShowMCForm(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
          >
            + {t('new_machine_center') || 'Nova Máquina'}
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('total_work_centers') || 'Work Centers Totais'}</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{workCenters.length}</div>
          <div className="text-xs text-gray-500 mt-1">
            {workCenters.filter(wc => !wc.blocked).length} {t('active') || 'ativos'}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('total_machines') || 'Máquinas Totais'}</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{machineCenters.length}</div>
          <div className="text-xs text-gray-500 mt-1">
            {machineCenters.filter(mc => !mc.blocked).length} {t('active') || 'ativas'}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('total_capacity') || 'Capacidade Total'}</div>
          <div className="text-2xl font-bold text-purple-600 mt-1">
            {getTotalCapacity().toLocaleString()} <span className="text-sm">min/dia</span>
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('avg_efficiency') || 'Eficiência Média'}</div>
          <div className={`text-2xl font-bold mt-1 ${getEfficiencyColor(getAvgEfficiency())}`}>
            {getAvgEfficiency().toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Work Centers List */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold mb-4">🏭 {t('work_centers') || 'Work Centers'}</h2>
        
        {workCenters.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">{t('no_work_centers') || 'Nenhum Work Center encontrado'}</p>
            <button
              onClick={() => setShowWCForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              + {t('create_first_wc') || 'Criar primeiro Work Center'}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {workCenters.map((wc) => {
              const machines = getMachinesForWC(wc.code)
              const isSelected = selectedWC === wc.code
              
              return (
                <div key={wc.id} className="border rounded-lg overflow-hidden">
                  {/* Work Center Header */}
                  <div
                    onClick={() => setSelectedWC(isSelected ? null : wc.code)}
                    className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-lg">{wc.code}</h3>
                          <span className="text-sm text-gray-600">{wc.name}</span>
                          {wc.blocked && (
                            <span className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded">
                              🔒 {t('blocked') || 'Bloqueado'}
                            </span>
                          )}
                        </div>
                        <div className="mt-2 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                          <div>
                            <span className="text-gray-500">{t('capacity') || 'Capacidade'}:</span>
                            <span className="ml-1 font-medium">{wc.capacity} min/dia</span>
                          </div>
                          <div>
                            <span className="text-gray-500">{t('efficiency') || 'Eficiência'}:</span>
                            <span className={`ml-1 font-medium ${getEfficiencyColor(wc.efficiency_pct)}`}>
                              {wc.efficiency_pct}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">{t('unit_cost') || 'Custo/min'}:</span>
                            <span className="ml-1 font-medium">€{wc.unit_cost.toFixed(2)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">{t('overhead') || 'Overhead'}:</span>
                            <span className="ml-1 font-medium">{wc.overhead_rate}%</span>
                          </div>
                          <div>
                            <span className="text-gray-500">{t('machines') || 'Máquinas'}:</span>
                            <span className="ml-1 font-medium">{machines.length}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            alert(`Edit ${wc.code} - Coming soon!`)
                          }}
                          className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                        >
                          ✏️ {t('edit') || 'Editar'}
                        </button>
                        <span className="text-gray-400">{isSelected ? '▼' : '▶'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Machine Centers (collapsed) */}
                  {isSelected && machines.length > 0 && (
                    <div className="bg-gray-50 border-t px-4 py-3">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">
                        ⚙️ {t('machine_centers') || 'Machine Centers'} ({machines.length})
                      </h4>
                      <div className="space-y-2">
                        {machines.map((mc) => (
                          <div key={mc.id} className="bg-white p-3 rounded border">
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{mc.code}</span>
                                  <span className="text-sm text-gray-600">{mc.name}</span>
                                  {mc.blocked && (
                                    <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-800 rounded">
                                      🔒
                                    </span>
                                  )}
                                </div>
                                <div className="mt-1 flex items-center gap-4 text-xs text-gray-600">
                                  <span>
                                    {t('capacity') || 'Capacidade'}: {mc.capacity} min/dia
                                  </span>
                                  <span className={getEfficiencyColor(mc.efficiency_pct)}>
                                    {t('efficiency') || 'Eficiência'}: {mc.efficiency_pct}%
                                  </span>
                                  <span>
                                    {t('cost') || 'Custo'}: €{mc.unit_cost.toFixed(2)}/min
                                  </span>
                                </div>
                              </div>
                              <button
                                onClick={() => setShowMCForm(true)}
                                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                              >
                                ✏️
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* No machines message */}
                  {isSelected && machines.length === 0 && (
                    <div className="bg-gray-50 border-t px-4 py-3 text-center">
                      <p className="text-sm text-gray-500 mb-2">
                        {t('no_machines_in_wc') || 'Nenhuma máquina neste Work Center'}
                      </p>
                      <button
                        onClick={() => alert(`Add machine to ${wc.code} - Coming soon!`)}
                        className="text-xs px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                      >
                        + {t('add_machine') || 'Adicionar Máquina'}
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Capacity Overview Chart (placeholder) */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold mb-4">📊 {t('capacity_overview') || 'Visão Geral de Capacidade'}</h2>
        <div className="space-y-3">
          {workCenters.filter(wc => !wc.blocked).map((wc) => {
            const utilizationPct = 65 // Placeholder - future: calculate from production orders
            return (
              <div key={wc.id}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{wc.code}</span>
                  <span className="text-sm text-gray-600">{utilizationPct}% {t('utilized') || 'utilizado'}</span>
                </div>
                <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all"
                    style={{ width: `${utilizationPct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
        <p className="text-xs text-gray-500 mt-4 italic">
          * {t('utilization_calculated') || 'Utilização calculada com base em Production Orders (placeholder)'}
        </p>
      </div>

      {showWCForm && (
        <WorkCenterForm
          onSuccess={() => { setShowWCForm(false); loadData() }}
          onCancel={() => setShowWCForm(false)}
        />
      )}
      {showMCForm && (
        <MachineCenterForm
          onSuccess={() => { setShowMCForm(false); loadData() }}
          onCancel={() => setShowMCForm(false)}
        />
      )}
    </div>
  )
}
