import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'

interface Task {
  id: string
  order_no: string
  operation_no: number
  item_no: string
  work_center_code: string
  priority: string
  status: string
  assigned_to?: string
}

export default function ProductionTasks() {
  const { t } = useTranslation()
  
  // Mock data
  const [tasks] = useState<Task[]>([
    {
      id: '1',
      order_no: 'PO-2025-001',
      operation_no: 10,
      item_no: 'FG-CHAIR-001',
      work_center_code: 'MACHINING',
      priority: 'High',
      status: 'Ready',
      assigned_to: undefined
    },
    {
      id: '2',
      order_no: 'PO-2025-002',
      operation_no: 10,
      item_no: 'FG-TABLE-001',
      work_center_code: 'ASSEMBLY',
      priority: 'Normal',
      status: 'Assigned',
      assigned_to: 'OPER-001'
    }
  ])

  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterWC, setFilterWC] = useState<string>('all')

  const filteredTasks = tasks.filter(t => {
    if (filterStatus !== 'all' && t.status !== filterStatus) return false
    if (filterWC !== 'all' && t.work_center_code !== filterWC) return false
    return true
  })

  const getStatusColor = (status: string) => {
    const colors = {
      'Ready': 'bg-green-100 text-green-800',
      'Assigned': 'bg-blue-100 text-blue-800',
      'In Progress': 'bg-yellow-100 text-yellow-800',
      'Completed': 'bg-gray-100 text-gray-800'
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const getPriorityColor = (priority: string) => {
    const colors = {
      'High': 'text-red-600',
      'Normal': 'text-blue-600',
      'Low': 'text-gray-600'
    }
    return colors[priority as keyof typeof colors] || 'text-gray-600'
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">✅ {t('tasks') || 'Tarefas de Produção'}</h1>
          <p className="text-sm text-gray-600 mt-1">
            {t('tasks_desc') || 'Fila de tarefas para operadores'}
          </p>
        </div>
        <button
          onClick={() => toast('🔮 This feature will be available in Phase C', { icon: 'ℹ️' })}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          ➕ {t('assign_task') || 'Atribuir Tarefa'}
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('ready') || 'Prontas'}</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {tasks.filter(t => t.status === 'Ready').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('assigned') || 'Atribuídas'}</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {tasks.filter(t => t.status === 'Assigned').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('in_progress') || 'Em Progresso'}</div>
          <div className="text-2xl font-bold text-yellow-600 mt-1">
            {tasks.filter(t => t.status === 'In Progress').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">{t('high_priority') || 'Alta Prioridade'}</div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {tasks.filter(t => t.priority === 'High').length}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex gap-4">
          <div>
            <label className="text-sm text-gray-600 mb-1 block">{t('status') || 'Estado'}</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="all">{t('all') || 'Todos'}</option>
              <option value="Ready">{t('ready') || 'Prontas'}</option>
              <option value="Assigned">{t('assigned') || 'Atribuídas'}</option>
              <option value="In Progress">{t('in_progress') || 'Em Progresso'}</option>
              <option value="Completed">{t('completed') || 'Concluídas'}</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">{t('work_center') || 'Centro de Trabalho'}</label>
            <select
              value={filterWC}
              onChange={(e) => setFilterWC(e.target.value)}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="all">{t('all') || 'Todos'}</option>
              <option value="MACHINING">MACHINING</option>
              <option value="ASSEMBLY">ASSEMBLY</option>
              <option value="FINISHING">FINISHING</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tasks List */}
      <div className="space-y-3">
        {filteredTasks.map(task => (
          <div key={task.id} className="card p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold">{task.order_no}</span>
                  <span className="text-gray-600">Op {task.operation_no}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                    {task.status}
                  </span>
                  <span className={`text-sm font-medium ${getPriorityColor(task.priority)}`}>
                    🔥 {task.priority}
                  </span>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>📦 Item: <span className="font-medium">{task.item_no}</span></div>
                  <div>🏭 Work Center: <span className="font-medium">{task.work_center_code}</span></div>
                  {task.assigned_to && (
                    <div>👤 Assigned to: <span className="font-medium">{task.assigned_to}</span></div>
                  )}
                </div>
              </div>
              
              <div className="flex gap-2">
                {task.status === 'Ready' && (
                  <button
                    onClick={() => toast('🔮 Task assignment will be available in Phase C', { icon: 'ℹ️' })}
                    className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                  >
                    👤 Assign
                  </button>
                )}
                {task.status === 'Assigned' && (
                  <button
                    onClick={() => toast('🔮 Task execution tracking will be available in Phase C', { icon: 'ℹ️' })}
                    className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                  >
                    ▶️ Start
                  </button>
                )}
                {task.status === 'In Progress' && (
                  <button
                    onClick={() => toast('🔮 Task pause/resume will be available in Phase C', { icon: 'ℹ️' })}
                    className="px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm"
                  >
                    ⏸️ Pause
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Coming Soon */}
      <div className="card p-4">
        <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <p className="text-sm text-purple-800">
            🔮 <strong>{t('coming_soon') || 'Em breve'}:</strong> Task assignment automático, operator dashboard, real-time status updates, integration com Production Execution.
          </p>
        </div>
      </div>
    </div>
  )
}
