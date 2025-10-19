import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

interface BOM {
  id: string
  item_no: string
  version_code: string
  status: string
  base_uom: string
  lines: any[]
  created_at: string
}

interface Routing {
  id: string
  item_no: string
  version_code: string
  status: string
  operations: any[]
  created_at: string
}

export default function ProductionDesign() {
  const { t } = useTranslation()
  const [boms, setBOMs] = useState<BOM[]>([])
  const [routings, setRoutings] = useState<Routing[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'boms' | 'routings'>('boms')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [bomsRes, routingsRes] = await Promise.all([
        api.get('/api/production/boms'),
        api.get('/api/production/routings')
      ])
      setBOMs(bomsRes.data)
      setRoutings(routingsRes.data)
    } catch (error) {
      console.error('Failed to load production design data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const colors = {
      'New': 'bg-gray-100 text-gray-800',
      'Under Development': 'bg-blue-100 text-blue-800',
      'Certified': 'bg-green-100 text-green-800',
      'Closed': 'bg-red-100 text-red-800'
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'
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
          <h1 className="text-xl font-semibold">🎨 {t('product_design') || 'Design de Produtos'}</h1>
          <p className="text-sm text-gray-600 mt-1">
            {t('product_design_desc') || 'Gestão de BOMs (Bills of Materials) e Routings (Rotas de Produção)'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => alert('Create BOM - Coming soon!')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            + {t('new_bom') || 'Nova BOM'}
          </button>
          <button
            onClick={() => alert('Create Routing - Coming soon!')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
          >
            + {t('new_routing') || 'Novo Routing'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('boms')}
            className={`px-4 py-2 border-b-2 transition-colors ${
              activeTab === 'boms'
                ? 'border-blue-600 text-blue-600 font-semibold'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            📋 BOMs ({boms.length})
          </button>
          <button
            onClick={() => setActiveTab('routings')}
            className={`px-4 py-2 border-b-2 transition-colors ${
              activeTab === 'routings'
                ? 'border-blue-600 text-blue-600 font-semibold'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            🛤️ Routings ({routings.length})
          </button>
        </div>
      </div>

      {/* BOMs Tab */}
      {activeTab === 'boms' && (
        <div className="space-y-3">
          {boms.length === 0 ? (
            <div className="card p-8 text-center">
              <p className="text-gray-500 mb-4">
                {t('no_boms_found') || 'Nenhuma BOM encontrada'}
              </p>
              <button
                onClick={() => alert('Create BOM - Coming soon!')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                + {t('create_first_bom') || 'Criar primeira BOM'}
              </button>
            </div>
          ) : (
            boms.map((bom) => (
              <div key={bom.id} className="card p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-lg">{bom.item_no}</h3>
                      <span className="text-sm text-gray-500">v{bom.version_code}</span>
                      <span className={`text-xs px-2 py-1 rounded ${getStatusBadge(bom.status)}`}>
                        {bom.status}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                      <span>📦 {bom.base_uom}</span>
                      <span>🔗 {bom.lines.length} {t('components') || 'componentes'}</span>
                      <span>📅 {new Date(bom.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => alert(`View BOM ${bom.item_no} - Coming soon!`)}
                      className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    >
                      👁️ {t('view') || 'Ver'}
                    </button>
                    {bom.status === 'Certified' && (
                      <button
                        onClick={async () => {
                          try {
                            const quantity = prompt('Quantity to explode:', '10')
                            if (!quantity) return
                            const res = await api.post(`/api/production/boms/${bom.id}/explode?quantity=${quantity}`)
                            console.log('Explosion result:', res.data)
                            alert(`BOM Explosion successful!\n\nComponents: ${Object.keys(res.data.consolidated_components).length}\nMax Level: ${res.data.max_level}`)
                          } catch (error) {
                            console.error('Explosion failed:', error)
                            alert('Failed to explode BOM')
                          }
                        }}
                        className="px-3 py-1.5 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded transition-colors"
                      >
                        💥 {t('explode') || 'Explodir'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Routings Tab */}
      {activeTab === 'routings' && (
        <div className="space-y-3">
          {routings.length === 0 ? (
            <div className="card p-8 text-center">
              <p className="text-gray-500 mb-4">
                {t('no_routings_found') || 'Nenhum Routing encontrado'}
              </p>
              <button
                onClick={() => alert('Create Routing - Coming soon!')}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                + {t('create_first_routing') || 'Criar primeiro Routing'}
              </button>
            </div>
          ) : (
            routings.map((routing) => (
              <div key={routing.id} className="card p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-lg">{routing.item_no}</h3>
                      <span className="text-sm text-gray-500">v{routing.version_code}</span>
                      <span className={`text-xs px-2 py-1 rounded ${getStatusBadge(routing.status)}`}>
                        {routing.status}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                      <span>⚙️ {routing.operations.length} {t('operations') || 'operações'}</span>
                      <span>📅 {new Date(routing.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => alert(`View Routing ${routing.item_no} - Coming soon!`)}
                      className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    >
                      👁️ {t('view') || 'Ver'}
                    </button>
                    {routing.status === 'Certified' && (
                      <button
                        onClick={async () => {
                          try {
                            const quantity = prompt('Quantity to calculate time:', '10')
                            if (!quantity) return
                            const res = await api.post(`/api/production/routings/${routing.id}/calculate-time?quantity=${quantity}`)
                            console.log('Time calculation:', res.data)
                            alert(`Time Calculation:\n\nSetup: ${res.data.total_setup_time} min\nRun: ${res.data.total_run_time} min\nTotal: ${res.data.total_time} min`)
                          } catch (error) {
                            console.error('Time calculation failed:', error)
                            alert('Failed to calculate time')
                          }
                        }}
                        className="px-3 py-1.5 text-sm bg-green-600 text-white hover:bg-green-700 rounded transition-colors"
                      >
                        ⏱️ {t('calc_time') || 'Calcular Tempo'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('certified_boms') || 'BOMs Certificadas'}</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {boms.filter(b => b.status === 'Certified').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('certified_routings') || 'Routings Certificados'}</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {routings.filter(r => r.status === 'Certified').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('in_development') || 'Em Desenvolvimento'}</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {boms.filter(b => b.status === 'Under Development').length + 
             routings.filter(r => r.status === 'Under Development').length}
          </div>
        </div>
      </div>
    </div>
  )
}
