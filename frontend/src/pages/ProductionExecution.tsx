import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../lib/api'
import JournalPostingModal from '../components/JournalPostingModal'

interface Operation {
  order_no: string
  item_no: string
  operation_no: number
  work_center_code: string
  machine_center_code?: string
  status: string
  setup_time: number
  run_time: number
  quantity: number
}

export default function ProductionExecution() {
  const { t } = useTranslation()
  const [operations, setOperations] = useState<Operation[]>([])
  const [loading, setLoading] = useState(true)
  const [showJournalModal, setShowJournalModal] = useState(false)
  const [selectedOperation, setSelectedOperation] = useState<Operation | null>(null)

  useEffect(() => {
    // Placeholder - future: load from /api/production/operations
    setLoading(false)
    // Mock data
    setOperations([
      {
        order_no: 'PO-2025-001',
        item_no: 'FG-CHAIR-001',
        operation_no: 10,
        work_center_code: 'MACHINING',
        machine_center_code: 'CNC-001',
        status: 'Ready',
        setup_time: 30,
        run_time: 80,
        quantity: 10
      },
      {
        order_no: 'PO-2025-001',
        item_no: 'FG-CHAIR-001',
        operation_no: 20,
        work_center_code: 'ASSEMBLY',
        status: 'Waiting',
        setup_time: 15,
        run_time: 120,
        quantity: 10
      }
    ])
  }, [])

  const getStatusColor = (status: string) => {
    const colors = {
      'Ready': 'bg-green-100 text-green-800',
      'In Progress': 'bg-yellow-100 text-yellow-800',
      'Completed': 'bg-blue-100 text-blue-800',
      'Waiting': 'bg-gray-100 text-gray-800'
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
      <div>
        <h1 className="text-xl font-semibold">🔨 {t('execution') || 'Execução de Produção'}</h1>
        <p className="text-sm text-gray-600 mt-1">
          {t('execution_desc') || 'Shop Floor Interface - Controlo de operações em tempo real'}
        </p>
      </div>

      {/* Shop Floor Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('ready_to_start') || 'Prontas'}</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {operations.filter(o => o.status === 'Ready').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('in_progress') || 'Em Curso'}</div>
          <div className="text-2xl font-bold text-yellow-600 mt-1">
            {operations.filter(o => o.status === 'In Progress').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('completed_today') || 'Completadas Hoje'}</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {operations.filter(o => o.status === 'Completed').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('waiting') || 'Aguardam'}</div>
          <div className="text-2xl font-bold text-gray-600 mt-1">
            {operations.filter(o => o.status === 'Waiting').length}
          </div>
        </div>
      </div>

      {/* Operations Queue */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold mb-4">📋 {t('operations_queue') || 'Fila de Operações'}</h2>
        
        {operations.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">{t('no_operations') || 'Nenhuma operação na fila'}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {operations.map((op, idx) => (
              <div key={idx} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-gray-400">#{op.operation_no}</span>
                      <div>
                        <h3 className="font-semibold">{op.order_no}</h3>
                        <p className="text-sm text-gray-600">{op.item_no}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded ${getStatusColor(op.status)}`}>
                        {op.status}
                      </span>
                    </div>

                    <div className="mt-3 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                      <div>
                        <span className="text-gray-500">{t('work_center') || 'Work Center'}:</span>
                        <span className="ml-1 font-medium">{op.work_center_code}</span>
                      </div>
                      {op.machine_center_code && (
                        <div>
                          <span className="text-gray-500">{t('machine') || 'Máquina'}:</span>
                          <span className="ml-1 font-medium">{op.machine_center_code}</span>
                        </div>
                      )}
                      <div>
                        <span className="text-gray-500">{t('setup') || 'Setup'}:</span>
                        <span className="ml-1 font-medium">{op.setup_time} min</span>
                      </div>
                      <div>
                        <span className="text-gray-500">{t('run') || 'Run'}:</span>
                        <span className="ml-1 font-medium">{op.run_time} min</span>
                      </div>
                      <div>
                        <span className="text-gray-500">{t('quantity') || 'Qty'}:</span>
                        <span className="ml-1 font-medium">{op.quantity}</span>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-col gap-2 ml-4">
                    {op.status === 'Ready' && (
                      <button
                        onClick={() => {
                          setSelectedOperation(op)
                          setShowJournalModal(true)
                        }}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                      >
                        ▶️ {t('start') || 'Iniciar'}
                      </button>
                    )}
                    {op.status === 'In Progress' && (
                      <>
                        <button
                          onClick={() => alert('Pause operation - Coming soon!')}
                          className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors text-sm"
                        >
                          ⏸️ {t('pause') || 'Pausar'}
                        </button>
                        <button
                          onClick={() => {
                            setSelectedOperation(op)
                            setShowJournalModal(true)
                          }}
                          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                        >
                          ✅ {t('complete') || 'Completar'}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Journal Posting Section */}
      <div className="card p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">📝 {t('journal_posting') || 'Lançamento de Journals'}</h2>
          <div className="flex gap-2">
            <button
              onClick={() => {
                // Use first operation as default if none selected
                setSelectedOperation(operations[0] || null)
                setShowJournalModal(true)
              }}
              disabled={operations.length === 0}
              className="px-3 py-1.5 bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors text-sm disabled:opacity-50"
            >
              📉 {t('consumption') || 'Consumo'}
            </button>
            <button
              onClick={() => {
                setSelectedOperation(operations[0] || null)
                setShowJournalModal(true)
              }}
              disabled={operations.length === 0}
              className="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm disabled:opacity-50"
            >
              📈 {t('output') || 'Output'}
            </button>
            <button
              onClick={() => {
                setSelectedOperation(operations[0] || null)
                setShowJournalModal(true)
              }}
              disabled={operations.length === 0}
              className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm disabled:opacity-50"
            >
              ⏱️ {t('capacity') || 'Capacidade'}
            </button>
          </div>
        </div>
        <p className="text-sm text-gray-600">
          {t('journal_posting_desc') || 'Lançar movimentos de consumo de materiais, output de produtos finalizados e tempo de capacidade utilizado.'}
        </p>
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            ✅ <strong>{t('phase_c') || 'Fase C'}:</strong> Production Journals completamente funcional com posting idempotente
          </p>
        </div>
      </div>

      {/* Journal Posting Modal */}
      {showJournalModal && selectedOperation && (
        <JournalPostingModal
          operation={selectedOperation}
          onSuccess={() => {
            setShowJournalModal(false)
            setSelectedOperation(null)
            // Reload operations (in real app)
          }}
          onCancel={() => {
            setShowJournalModal(false)
            setSelectedOperation(null)
          }}
        />
      )}
    </div>
  )
}
