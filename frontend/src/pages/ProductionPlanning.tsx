import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../lib/api'

interface ProductionOrder {
  id: string
  order_no: string
  item_no: string
  item_description: string
  quantity: number
  uom_code: string
  status: string
  due_date: string
  bom_version_code?: string
  routing_version_code?: string
  created_at: string
}

export default function ProductionPlanning() {
  const { t } = useTranslation()
  const [orders, setOrders] = useState<ProductionOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<string>('all')

  useEffect(() => {
    loadOrders()
  }, [])

  const loadOrders = async () => {
    try {
      setLoading(true)
      const data = await api<ProductionOrder[]>('/api/production/production-orders')
      setOrders(data)
    } catch (error) {
      console.error('Failed to load production orders:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const colors = {
      'Planned': 'bg-gray-100 text-gray-800',
      'Released': 'bg-blue-100 text-blue-800',
      'In Progress': 'bg-yellow-100 text-yellow-800',
      'Finished': 'bg-green-100 text-green-800',
      'Closed': 'bg-gray-300 text-gray-700'
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const releaseOrder = async (orderId: string) => {
    if (!confirm('Release this production order?')) return
    try {
      await api(`/api/production/production-orders/${orderId}/release`, { method: 'POST' })
      alert('Production order released!')
      loadOrders()
    } catch (error: any) {
      alert(`Failed to release: ${error.message}`)
    }
  }

  const finishOrder = async (orderId: string) => {
    if (!confirm('Finish this production order?')) return
    try {
      await api(`/api/production/production-orders/${orderId}/finish`, { method: 'POST' })
      alert('Production order finished!')
      loadOrders()
    } catch (error: any) {
      alert(`Failed to finish: ${error.message}`)
    }
  }

  const cancelOrder = async (orderId: string) => {
    if (!confirm('Cancel this production order? This action cannot be undone!')) return
    try {
      await api(`/api/production/production-orders/${orderId}/cancel`, { method: 'POST' })
      alert('Production order cancelled!')
      loadOrders()
    } catch (error: any) {
      alert(`Failed to cancel: ${error.message}`)
    }
  }

  const filteredOrders = filterStatus === 'all' 
    ? orders 
    : orders.filter(o => o.status === filterStatus)

  const getOrdersByStatus = (status: string) => {
    return orders.filter(o => o.status === status).length
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
          <h1 className="text-xl font-semibold">📅 {t('planning') || 'Planeamento de Produção'}</h1>
          <p className="text-sm text-gray-600 mt-1">
            {t('planning_desc') || 'Gestão de Production Orders e MPS/MRP'}
          </p>
        </div>
        <button
          onClick={() => alert('Create Production Order - Coming soon!')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          + {t('new_production_order') || 'Nova Ordem de Produção'}
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="card p-3">
          <div className="text-xs text-gray-600">{t('planned') || 'Planeadas'}</div>
          <div className="text-2xl font-bold text-gray-600 mt-1">{getOrdersByStatus('Planned')}</div>
        </div>
        <div className="card p-3">
          <div className="text-xs text-gray-600">{t('released') || 'Lançadas'}</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{getOrdersByStatus('Released')}</div>
        </div>
        <div className="card p-3">
          <div className="text-xs text-gray-600">{t('in_progress') || 'Em Curso'}</div>
          <div className="text-2xl font-bold text-yellow-600 mt-1">{getOrdersByStatus('In Progress')}</div>
        </div>
        <div className="card p-3">
          <div className="text-xs text-gray-600">{t('finished') || 'Finalizadas'}</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{getOrdersByStatus('Finished')}</div>
        </div>
        <div className="card p-3">
          <div className="text-xs text-gray-600">{t('closed') || 'Fechadas'}</div>
          <div className="text-2xl font-bold text-gray-400 mt-1">{getOrdersByStatus('Closed')}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700 pb-2 overflow-x-auto">
        {['all', 'Planned', 'Released', 'In Progress', 'Finished'].map((status) => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`px-4 py-2 text-sm rounded-t transition-colors whitespace-nowrap ${
              filterStatus === status
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status === 'all' ? t('all') || 'Todas' : status}
            {status !== 'all' && <span className="ml-1">({getOrdersByStatus(status)})</span>}
          </button>
        ))}
      </div>

      {/* Production Orders List */}
      <div className="space-y-3">
        {filteredOrders.length === 0 ? (
          <div className="card p-8 text-center">
            <p className="text-gray-500 mb-4">
              {filterStatus === 'all' 
                ? t('no_production_orders') || 'Nenhuma ordem de produção encontrada'
                : `No ${filterStatus} orders`
              }
            </p>
            <button
              onClick={() => alert('Create Production Order - Coming soon!')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              + {t('create_first_order') || 'Criar primeira ordem'}
            </button>
          </div>
        ) : (
          filteredOrders.map((order) => (
            <div key={order.id} className="card p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-lg">{order.order_no}</h3>
                    <span className={`text-xs px-2 py-1 rounded ${getStatusBadge(order.status)}`}>
                      {order.status}
                    </span>
                  </div>
                  
                  <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="text-gray-500">{t('item') || 'Item'}:</span>
                      <span className="ml-1 font-medium">{order.item_no}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">{t('quantity') || 'Quantidade'}:</span>
                      <span className="ml-1 font-medium">{order.quantity} {order.uom_code}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">{t('due_date') || 'Data Limite'}:</span>
                      <span className="ml-1 font-medium">
                        {new Date(order.due_date).toLocaleDateString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">{t('versions') || 'Versões'}:</span>
                      <span className="ml-1 font-medium text-xs">
                        BOM: {order.bom_version_code || 'N/A'} | 
                        Routing: {order.routing_version_code || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {order.item_description && (
                    <p className="mt-2 text-sm text-gray-600">{order.item_description}</p>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-2 ml-4">
                  {order.status === 'Planned' && (
                    <button
                      onClick={() => releaseOrder(order.id)}
                      className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                      🚀 {t('release') || 'Lançar'}
                    </button>
                  )}
                  
                  {order.status === 'Released' && (
                    <button
                      onClick={() => finishOrder(order.id)}
                      className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                    >
                      ✅ {t('finish') || 'Finalizar'}
                    </button>
                  )}

                  {['Planned', 'Released'].includes(order.status) && (
                    <button
                      onClick={() => cancelOrder(order.id)}
                      className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                    >
                      ❌ {t('cancel') || 'Cancelar'}
                    </button>
                  )}

                  <button
                    onClick={() => alert(`View ${order.order_no} - Coming soon!`)}
                    className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                  >
                    👁️ {t('view') || 'Ver'}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* MRP Section (placeholder) */}
      <div className="card p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">🤖 {t('mrp_planning') || 'Planeamento MRP'}</h2>
          <button
            onClick={() => alert('MRP Run - Coming in Phase B!')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
          >
            ▶️ {t('run_mrp') || 'Executar MRP'}
          </button>
        </div>
        <p className="text-sm text-gray-600">
          {t('mrp_desc') || 'Material Requirements Planning automático: calcula necessidades líquidas, gera propostas de produção e compras.'}
        </p>
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            ℹ️ <strong>{t('coming_soon') || 'Em breve'}:</strong> MPS (Master Production Schedule), Net Requirements Calculation, Purchase Requisitions, RCCP (Capacity Alerts)
          </p>
        </div>
      </div>
    </div>
  )
}
