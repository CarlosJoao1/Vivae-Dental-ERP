import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

interface ProductionOrderDetailsProps {
  orderId: string
  onClose: () => void
}

interface ProductionOrderDetails {
  id: string
  order_no: string
  item_no: string
  item_description: string
  description?: string
  quantity: number
  uom_code: string
  status: string
  start_date?: string
  due_date: string
  location_code?: string
  priority?: number
  bom_version_code?: string
  routing_version_code?: string
  created_at: string
  created_by?: string
  updated_at?: string
  updated_by?: string
  lines?: ProductionOrderLine[]
  routing_operations?: RoutingOperation[]
  costs?: OrderCosts
}

interface ProductionOrderLine {
  id: string
  line_no: number
  item_no: string
  description: string
  quantity: number
  uom_code: string
  unit_cost?: number
  total_cost?: number
}

interface RoutingOperation {
  id: string
  operation_no: number
  work_center_code: string
  description: string
  setup_time_minutes: number
  run_time_minutes: number
  status: string
}

interface OrderCosts {
  material_cost: number
  labor_cost: number
  overhead_cost: number
  total_cost: number
}

export default function ProductionOrderDetailsModal({ orderId, onClose }: ProductionOrderDetailsProps) {
  const { t } = useTranslation()
  const [order, setOrder] = useState<ProductionOrderDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'general' | 'lines' | 'routing' | 'costs' | 'audit'>('general')

  useEffect(() => {
    loadOrderDetails()
  }, [orderId])

  const loadOrderDetails = async () => {
    setLoading(true)
    try {
      const data = await api<ProductionOrderDetails>(`/api/production/production-orders/${orderId}`)
      setOrder(data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      toast.error(`Failed to load order details: ${errorMessage}`)
      onClose()
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      'Planned': 'bg-gray-100 text-gray-800',
      'Released': 'bg-blue-100 text-blue-800',
      'In Progress': 'bg-yellow-100 text-yellow-800',
      'Finished': 'bg-green-100 text-green-800',
      'Closed': 'bg-gray-300 text-gray-700'
    }
    return styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatCurrency = (amount?: number) => {
    if (amount === undefined || amount === null) return '-'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount)
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl p-8">
          <div className="text-center">
            <div className="animate-spin text-4xl mb-4">⏳</div>
            <p className="text-gray-600">Loading order details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!order) {
    return null
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b bg-gradient-to-r from-blue-50 to-white flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold text-gray-800">
                📦 {order.order_no}
              </h2>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(order.status)}`}>
                {order.status}
              </span>
            </div>
            <p className="text-gray-600">
              <strong>{order.item_no}</strong> - {order.item_description}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              📍 {order.location_code || 'No location'} | 
              📊 {order.quantity} {order.uom_code} | 
              📅 Due: {formatDate(order.due_date)}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b bg-gray-50">
          <div className="flex px-6">
            {[
              { key: 'general', label: '📋 General', icon: '📋' },
              { key: 'lines', label: '📝 Lines', icon: '📝', count: order.lines?.length },
              { key: 'routing', label: '🔄 Routing', icon: '🔄', count: order.routing_operations?.length },
              { key: 'costs', label: '💰 Costs', icon: '💰' },
              { key: 'audit', label: '🔍 Audit', icon: '🔍' }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`px-4 py-3 text-sm font-medium transition-colors relative ${
                  activeTab === tab.key
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-600 rounded-full text-xs">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'general' && (
            <div className="space-y-6">
              {/* Order Information */}
              <div className="grid grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">Order Number</label>
                  <p className="text-lg font-semibold">{order.order_no}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">Status</label>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(order.status)}`}>
                    {order.status}
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">Priority</label>
                  <p className="text-lg">{order.priority || 0}</p>
                </div>
              </div>

              {/* Item Information */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold mb-4">📦 Item Information</h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Item No.</label>
                    <p className="text-lg font-mono">{order.item_no}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Description</label>
                    <p className="text-lg">{order.item_description}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Quantity</label>
                    <p className="text-lg font-semibold">{order.quantity} {order.uom_code}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Location</label>
                    <p className="text-lg">{order.location_code || '-'}</p>
                  </div>
                </div>
              </div>

              {/* Dates */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold mb-4">📅 Dates</h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Start Date</label>
                    <p className="text-lg">{formatDate(order.start_date)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Due Date</label>
                    <p className="text-lg font-semibold text-red-600">{formatDate(order.due_date)}</p>
                  </div>
                </div>
              </div>

              {/* BOM & Routing */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold mb-4">🔧 Configuration</h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">BOM Version</label>
                    <p className="text-lg">{order.bom_version_code || '-'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Routing Version</label>
                    <p className="text-lg">{order.routing_version_code || '-'}</p>
                  </div>
                </div>
              </div>

              {/* Description */}
              {order.description && (
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold mb-4">📝 Description</h3>
                  <p className="text-gray-700 bg-gray-50 p-4 rounded-lg">{order.description}</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'lines' && (
            <div>
              {order.lines && order.lines.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Line</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Item No.</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Description</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Quantity</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Unit Cost</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {order.lines.map(line => (
                        <tr key={line.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium">{line.line_no}</td>
                          <td className="px-4 py-3 text-sm font-mono">{line.item_no}</td>
                          <td className="px-4 py-3 text-sm">{line.description}</td>
                          <td className="px-4 py-3 text-sm text-right">{line.quantity} {line.uom_code}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatCurrency(line.unit_cost)}</td>
                          <td className="px-4 py-3 text-sm text-right font-semibold">{formatCurrency(line.total_cost)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📭</div>
                  <p className="text-gray-600">No lines found for this production order</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'routing' && (
            <div>
              {order.routing_operations && order.routing_operations.length > 0 ? (
                <div className="space-y-4">
                  {order.routing_operations.map(op => (
                    <div key={op.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-semibold text-lg">
                            Operation {op.operation_no}: {op.description}
                          </h4>
                          <p className="text-sm text-gray-600">Work Center: {op.work_center_code}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          op.status === 'Completed' ? 'bg-green-100 text-green-800' :
                          op.status === 'In Progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {op.status}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 mt-3">
                        <div className="flex items-center text-sm">
                          <span className="text-gray-600">⏱️ Setup Time:</span>
                          <span className="ml-2 font-medium">{op.setup_time_minutes} min</span>
                        </div>
                        <div className="flex items-center text-sm">
                          <span className="text-gray-600">🏃 Run Time:</span>
                          <span className="ml-2 font-medium">{op.run_time_minutes} min</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🔄</div>
                  <p className="text-gray-600">No routing operations found for this production order</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'costs' && (
            <div>
              {order.costs ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                      <p className="text-sm text-blue-600 mb-1">Material Cost</p>
                      <p className="text-3xl font-bold text-blue-900">{formatCurrency(order.costs.material_cost)}</p>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                      <p className="text-sm text-green-600 mb-1">Labor Cost</p>
                      <p className="text-3xl font-bold text-green-900">{formatCurrency(order.costs.labor_cost)}</p>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                      <p className="text-sm text-yellow-600 mb-1">Overhead Cost</p>
                      <p className="text-3xl font-bold text-yellow-900">{formatCurrency(order.costs.overhead_cost)}</p>
                    </div>
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                      <p className="text-sm text-purple-600 mb-1">Total Cost</p>
                      <p className="text-3xl font-bold text-purple-900">{formatCurrency(order.costs.total_cost)}</p>
                    </div>
                  </div>

                  {/* Cost Breakdown Chart Placeholder */}
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold mb-4">📊 Cost Breakdown</h3>
                    <div className="bg-gray-50 rounded-lg p-8 text-center">
                      <p className="text-gray-600">Cost breakdown visualization coming soon</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">💰</div>
                  <p className="text-gray-600">No cost information available for this production order</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">Created At</label>
                  <p className="text-lg">{formatDateTime(order.created_at)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">Created By</label>
                  <p className="text-lg">{order.created_by || '-'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">Updated At</label>
                  <p className="text-lg">{formatDateTime(order.updated_at)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">Updated By</label>
                  <p className="text-lg">{order.updated_by || '-'}</p>
                </div>
              </div>

              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold mb-4">📝 Change History</h3>
                <div className="bg-gray-50 rounded-lg p-8 text-center">
                  <p className="text-gray-600">Change history tracking coming soon</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4 bg-gray-50 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
