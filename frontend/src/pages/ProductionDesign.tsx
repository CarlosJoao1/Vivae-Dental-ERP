import { useState, useEffect } from 'react'
// useTranslation already imported above
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import BOMForm from '../components/BOMForm'
import RoutingForm from '../components/RoutingForm'
import NumberInputDialog from '@/components/common/NumberInputDialog'

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
  const [showBOMForm, setShowBOMForm] = useState(false)
  const [showRoutingForm, setShowRoutingForm] = useState(false)
  const [selectedBOM, setSelectedBOM] = useState<BOM | undefined>(undefined)
  const [selectedRouting, setSelectedRouting] = useState<Routing | undefined>(undefined)
  const [quantityDialog, setQuantityDialog] = useState<{ open: boolean; mode: 'explode'|'time'; id: string; title: string }>(
    { open:false, mode:'explode', id:'', title:'' }
  )

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [bomsRes, routingsRes] = await Promise.all([
        api<BOM[]>('/api/production/boms'),
        api<Routing[]>('/api/production/routings')
      ])
      setBOMs(bomsRes)
      setRoutings(routingsRes)
    } catch (error) {
      console.error('Failed to load production design data:', error)
    } finally {
      setLoading(false)
    }
  }

  const seedDemo = async () => {
    const loading = toast.loading(String(t('seeding_demo') || 'Seeding demo BOM & Routing...'))
    try {
      // Ensure UOM PCS
      try {
        await api('/api/production/masterdata/uom', {
          method: 'POST',
          body: JSON.stringify({ code: 'PCS', description: 'Pieces', decimals: 0 })
        })
      } catch {}

      // Ensure Location MAIN
      try {
        await api('/api/production/masterdata/locations', {
          method: 'POST',
          body: JSON.stringify({ code: 'MAIN', name: 'Main Warehouse', is_default: true })
        })
      } catch {}

      // Ensure Work Center ASSEMBLY
      try {
        await api('/api/production/work-centers', {
          method: 'POST',
          body: JSON.stringify({ code: 'ASSEMBLY', name: 'Assembly', location_code: 'MAIN', capacity: 480, efficiency_pct: 100 })
        })
      } catch {}

      // Create component item (purchased)
      try {
        await api('/api/production/masterdata/items', {
          method: 'POST',
          body: JSON.stringify({ item_no: 'RM-DEMO-PLY', description: 'Demo Plywood', item_type: 'purchased', base_uom: 'PCS', status: 'Active' })
        })
      } catch {}

      // Create finished item (manufactured)
      try {
        await api('/api/production/masterdata/items', {
          method: 'POST',
          body: JSON.stringify({ item_no: 'FG-DEMO-001', description: 'Demo Finished Good', item_type: 'manufactured', base_uom: 'PCS', lead_time_days: 2, status: 'Active' })
        })
      } catch {}

      // Create BOM and certify
      const bom = await api<any>('/api/production/boms', {
        method: 'POST',
        body: JSON.stringify({
          item_no: 'FG-DEMO-001',
          version_code: 'V1',
          description: 'Demo BOM',
          status: 'Under Development',
          base_quantity: 1,
          base_uom: 'PCS',
          lines: [
            { line_no: 10, component_item_no: 'RM-DEMO-PLY', description: 'Plywood', quantity_per: 2, uom_code: 'PCS', scrap_pct: 0 }
          ]
        })
      })
      await api(`/api/production/boms/${bom.id}/certify`, { method: 'POST' })

      // Create Routing and certify
      const routing = await api<any>('/api/production/routings', {
        method: 'POST',
        body: JSON.stringify({
          item_no: 'FG-DEMO-001',
          version_code: 'V1',
          description: 'Demo Routing',
          status: 'Under Development',
          operations: [
            { operation_no: 10, work_center_code: 'ASSEMBLY', description: 'Assemble', setup_time: 10, run_time: 5, concurrent_capacities: 1 }
          ]
        })
      })
      await api(`/api/production/routings/${routing.id}/certify`, { method: 'POST' })

      toast.success(String(t('demo_seed_done') || 'Demo BOM and Routing created and certified'), { id: loading })
      loadData()
    } catch (e:any) {
      toast.error(e?.message || String(t('demo_seed_failed') || 'Failed to seed demo'), { id: loading })
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
            onClick={() => { setSelectedBOM(undefined); setShowBOMForm(true) }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            + {t('new_bom') || 'Nova BOM'}
          </button>
          <button
            onClick={() => { setSelectedRouting(undefined); setShowRoutingForm(true) }}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
          >
            + {t('new_routing') || 'Novo Routing'}
          </button>
          <button
            onClick={seedDemo}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
            title={String(t('quick_demo_seed_hint') || 'Creates demo FG item, BOM and Routing, and certifies them')}
          >
            ⚙️ {t('quick_demo_seed') || 'Quick Demo Seed'}
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
                      onClick={() => {
                        setSelectedBOM(bom)
                        setShowBOMForm(true)
                      }}
                      className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    >
                      ✏️ {t('edit') || 'Editar'}
                    </button>
                    {bom.status === 'Certified' && (
                      <button
                        onClick={() => setQuantityDialog({ open:true, mode:'explode', id:bom.id, title:String(t('explode')||'Explodir') })}
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
                      onClick={() => {
                        setSelectedRouting(routing)
                        setShowRoutingForm(true)
                      }}
                      className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    >
                      ✏️ {t('edit') || 'Editar'}
                    </button>
                    {routing.status === 'Certified' && (
                      <button
                        onClick={() => setQuantityDialog({ open:true, mode:'time', id:routing.id, title:String(t('calc_time')||'Calcular Tempo') })}
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
            <NumberInputDialog
              isOpen={quantityDialog.open}
              title={quantityDialog.title}
              initialValue={10}
              min={0.001}
              step={1}
              onCancel={() => setQuantityDialog(prev=>({ ...prev, open:false }))}
              onConfirm={async (qty)=>{
                try{
                  if (quantityDialog.mode === 'explode'){
                    const res = await api<any>(`/api/production/boms/${quantityDialog.id}/explode?quantity=${qty}`, { method: 'POST' })
                    toast.success(`✅ ${t('explode')||'Explodir'} OK (${Object.keys(res.consolidated_components||{}).length} comps)`)
                  } else {
                    const res = await api<any>(`/api/production/routings/${quantityDialog.id}/calculate-time?quantity=${qty}`, { method: 'POST' })
                    toast.success(`✅ ${t('calc_time')||'Calcular Tempo'} OK (${Math.round((res.total_time||0))} min)`) 
                  }
                } catch (e:any){
                  toast.error(e?.message || 'Operation failed')
                } finally {
                  setQuantityDialog(prev=>({ ...prev, open:false }))
                }
              }}
            />

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

      {/* Forms */}
      {showBOMForm && (
        <BOMForm
          bom={selectedBOM}
          onSuccess={() => {
            setShowBOMForm(false)
            setSelectedBOM(undefined)
            loadData()
          }}
          onCancel={() => {
            setShowBOMForm(false)
            setSelectedBOM(undefined)
          }}
        />
      )}

      {showRoutingForm && (
        <RoutingForm
          routing={selectedRouting}
          onSuccess={() => {
            setShowRoutingForm(false)
            setSelectedRouting(undefined)
            loadData()
          }}
          onCancel={() => {
            setShowRoutingForm(false)
            setSelectedRouting(undefined)
          }}
        />
      )}
    </div>
  )
}
