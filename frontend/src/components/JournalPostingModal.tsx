import { useState } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { api } from '@/lib/api'
import { v4 as uuidv4 } from 'uuid'

interface ConsumptionItem {
  item_no: string
  description: string
  quantity: number
  uom_code: string
}

interface JournalPostingModalProps {
  operation: any
  onSuccess: () => void
  onCancel: () => void
}

export default function JournalPostingModal({ operation, onSuccess, onCancel }: JournalPostingModalProps) {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'consumption' | 'output' | 'capacity'>('consumption')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  // Consumption form
  const consumptionForm = useForm<{ items: ConsumptionItem[] }>({
    defaultValues: {
      items: [{ item_no: '', description: '', quantity: 1, uom_code: 'UN' }]
    }
  })
  
  const { fields: consumptionFields, append: appendConsumption, remove: removeConsumption } = useFieldArray({
    control: consumptionForm.control,
    name: 'items'
  })
  
  // Output form
  const outputForm = useForm({
    defaultValues: {
      item_no: operation.item_no || '',
      quantity: operation.quantity || 1,
      uom_code: 'UN',
      description: ''
    }
  })
  
  // Capacity form
  const capacityForm = useForm({
    defaultValues: {
      setup_time: operation.setup_time || 0,
      run_time: operation.run_time || 0,
      stop_time: 0,
      scrap_time: 0,
      quantity: operation.quantity || 0,
      scrap_quantity: 0,
      operator_id: '',
      operator_name: ''
    }
  })
  
  const postConsumption = async (data: any) => {
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      const posting_id = uuidv4()
      
      const payload = {
        posting_id,
        production_order_no: operation.order_no,
        work_center_code: operation.work_center_code,
        operation_no: operation.operation_no,
        items: data.items,
        notes: `Material consumption for ${operation.order_no} Op ${operation.operation_no}`
      }
      
      const result = await api<{ posting_id: string; entries_created: number; already_posted?: boolean }>('/api/production/journals/consumption', {
        method: 'POST',
        body: JSON.stringify(payload)
      })
      
      if (result.already_posted) {
        setSuccess(`⚠️ Consumption already posted (idempotency check). Posting ID: ${result.posting_id}`)
      } else {
        setSuccess(`✅ Consumption posted successfully! ${result.entries_created} items recorded.`)
      }
      setTimeout(() => onSuccess(), 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to post consumption')
    } finally {
      setLoading(false)
    }
  }
  
  const postOutput = async (data: any) => {
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      const posting_id = uuidv4()
      
      const payload = {
        posting_id,
        production_order_no: operation.order_no,
        item_no: data.item_no,
        quantity: data.quantity,
        uom_code: data.uom_code,
        work_center_code: operation.work_center_code,
        operation_no: operation.operation_no,
        description: data.description,
        notes: `Output from ${operation.order_no} Op ${operation.operation_no}`
      }
      
      const result = await api<{ posting_id: string; entry_id?: number; already_posted?: boolean }>('/api/production/journals/output', {
        method: 'POST',
        body: JSON.stringify(payload)
      })
      
      if (result.already_posted) {
        setSuccess(`⚠️ Output already posted (idempotency check). Posting ID: ${result.posting_id}`)
      } else {
        setSuccess(`✅ Output posted successfully! Posting ID: ${result.posting_id}`)
      }
      setTimeout(() => onSuccess(), 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to post output')
    } finally {
      setLoading(false)
    }
  }
  
  const postCapacity = async (data: any) => {
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      const posting_id = uuidv4()
      
      const payload = {
        posting_id,
        production_order_no: operation.order_no,
        operation_no: operation.operation_no,
        work_center_code: operation.work_center_code,
        machine_center_code: operation.machine_center_code,
        item_no: operation.item_no,
        setup_time: data.setup_time,
        run_time: data.run_time,
        stop_time: data.stop_time,
        scrap_time: data.scrap_time,
        quantity: data.quantity,
        scrap_quantity: data.scrap_quantity,
        operator_id: data.operator_id,
        operator_name: data.operator_name,
        notes: `Capacity for ${operation.order_no} Op ${operation.operation_no}`
      }
      
      const result = await api<{ posting_id: string; entry_id?: number; already_posted?: boolean }>('/api/production/journals/capacity', {
        method: 'POST',
        body: JSON.stringify(payload)
      })
      
      if (result.already_posted) {
        setSuccess(`⚠️ Capacity already posted (idempotency check). Posting ID: ${result.posting_id}`)
      } else {
        setSuccess(`✅ Capacity posted successfully! Posting ID: ${result.posting_id}`)
      }
      setTimeout(() => onSuccess(), 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to post capacity')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">
            📝 {t('post_journal') || 'Post Production Journal'}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {operation.order_no} - Op {operation.operation_no} - {operation.work_center_code}
          </p>
        </div>
        
        {/* Tabs */}
        <div className="border-b px-6">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('consumption')}
              className={`px-4 py-2 border-b-2 transition-colors ${
                activeTab === 'consumption'
                  ? 'border-red-600 text-red-600 font-semibold'
                  : 'border-transparent text-gray-600 hover:text-gray-800'
              }`}
            >
              📦 {t('consumption') || 'Consumo'}
            </button>
            <button
              onClick={() => setActiveTab('output')}
              className={`px-4 py-2 border-b-2 transition-colors ${
                activeTab === 'output'
                  ? 'border-green-600 text-green-600 font-semibold'
                  : 'border-transparent text-gray-600 hover:text-gray-800'
              }`}
            >
              ✅ {t('output') || 'Produção'}
            </button>
            <button
              onClick={() => setActiveTab('capacity')}
              className={`px-4 py-2 border-b-2 transition-colors ${
                activeTab === 'capacity'
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-gray-600 hover:text-gray-800'
              }`}
            >
              ⏱️ {t('capacity') || 'Capacidade'}
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Error/Success Messages */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
              ❌ {error}
            </div>
          )}
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-800 text-sm">
              {success}
            </div>
          )}
          
          {/* Consumption Tab */}
          {activeTab === 'consumption' && (
            <form id="consumption-form" onSubmit={consumptionForm.handleSubmit(postConsumption)} className="space-y-4">
              <div className="mb-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">{t('material_consumption') || 'Consumo de Materiais'}</h3>
                  <button
                    type="button"
                    onClick={() => appendConsumption({ item_no: '', description: '', quantity: 1, uom_code: 'UN' })}
                    className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    ➕ {t('add_item') || 'Adicionar'}
                  </button>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {t('consumption_desc') || 'Registre os materiais consumidos nesta operação'}
                </p>
              </div>
              
              <div className="space-y-3">
                {consumptionFields.map((field: any, index: number) => (
                  <div key={field.id} className="border rounded-lg p-3 bg-gray-50">
                    <div className="grid grid-cols-12 gap-2">
                      <div className="col-span-4">
                        <label className="block text-xs font-medium mb-1">{t('item') || 'Item'}</label>
                        <input
                          type="text"
                          {...consumptionForm.register(`items.${index}.item_no`, { required: true })}
                          className="w-full px-2 py-1 border rounded text-sm"
                          placeholder="RM-001"
                        />
                      </div>
                      <div className="col-span-4">
                        <label className="block text-xs font-medium mb-1">{t('description') || 'Descrição'}</label>
                        <input
                          type="text"
                          {...consumptionForm.register(`items.${index}.description`)}
                          className="w-full px-2 py-1 border rounded text-sm"
                          placeholder="Material description"
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-xs font-medium mb-1">{t('quantity') || 'Qtd'}</label>
                        <input
                          type="number"
                          {...consumptionForm.register(`items.${index}.quantity`, { required: true, min: 0.001 })}
                          className="w-full px-2 py-1 border rounded text-sm"
                          step="0.001"
                        />
                      </div>
                      <div className="col-span-1">
                        <label className="block text-xs font-medium mb-1">{t('uom') || 'UM'}</label>
                        <input
                          type="text"
                          {...consumptionForm.register(`items.${index}.uom_code`)}
                          className="w-full px-2 py-1 border rounded text-sm"
                          placeholder="UN"
                        />
                      </div>
                      <div className="col-span-1 flex items-end">
                        <button
                          type="button"
                          onClick={() => removeConsumption(index)}
                          disabled={consumptionFields.length === 1}
                          className="w-full px-2 py-1 text-red-600 hover:text-red-800 disabled:text-gray-400"
                          title={t('remove') || 'Remover'}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </form>
          )}
          
          {/* Output Tab */}
          {activeTab === 'output' && (
            <form id="output-form" onSubmit={outputForm.handleSubmit(postOutput)} className="space-y-4">
              <div>
                <h3 className="font-semibold mb-1">{t('finished_goods_output') || 'Produção de Acabados'}</h3>
                <p className="text-xs text-gray-600">
                  {t('output_desc') || 'Registre a quantidade produzida nesta operação'}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    {t('item_no') || 'Item'} <span className="text-red-600">*</span>
                  </label>
                  <input
                    type="text"
                    {...outputForm.register('item_no', { required: true })}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="FG-CHAIR-001"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">{t('description') || 'Descrição'}</label>
                  <input
                    type="text"
                    {...outputForm.register('description')}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="Optional"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    {t('quantity') || 'Quantidade'} <span className="text-red-600">*</span>
                  </label>
                  <input
                    type="number"
                    {...outputForm.register('quantity', { required: true, min: 0.001 })}
                    className="w-full px-3 py-2 border rounded-lg"
                    step="0.001"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">{t('uom') || 'Unidade'}</label>
                  <input
                    type="text"
                    {...outputForm.register('uom_code')}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>
            </form>
          )}
          
          {/* Capacity Tab */}
          {activeTab === 'capacity' && (
            <form id="capacity-form" onSubmit={capacityForm.handleSubmit(postCapacity)} className="space-y-4">
              <div>
                <h3 className="font-semibold mb-1">{t('capacity_usage') || 'Uso de Capacidade'}</h3>
                <p className="text-xs text-gray-600">
                  {t('capacity_desc') || 'Registre os tempos gastos e informação do operador'}
                </p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">{t('setup_time') || 'Setup (min)'}</label>
                  <input
                    type="number"
                    {...capacityForm.register('setup_time', { min: 0 })}
                    className="w-full px-3 py-2 border rounded-lg"
                    step="0.1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">
                    {t('run_time') || 'Run (min)'} <span className="text-red-600">*</span>
                  </label>
                  <input
                    type="number"
                    {...capacityForm.register('run_time', { required: true, min: 0 })}
                    className="w-full px-3 py-2 border rounded-lg"
                    step="0.1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">{t('stop_time') || 'Paragem (min)'}</label>
                  <input
                    type="number"
                    {...capacityForm.register('stop_time', { min: 0 })}
                    className="w-full px-3 py-2 border rounded-lg"
                    step="0.1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">{t('scrap_time') || 'Refugo (min)'}</label>
                  <input
                    type="number"
                    {...capacityForm.register('scrap_time', { min: 0 })}
                    className="w-full px-3 py-2 border rounded-lg"
                    step="0.1"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">{t('quantity_produced') || 'Qtd Produzida'}</label>
                  <input
                    type="number"
                    {...capacityForm.register('quantity', { min: 0 })}
                    className="w-full px-3 py-2 border rounded-lg"
                    step="0.001"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">{t('scrap_quantity') || 'Qtd Refugo'}</label>
                  <input
                    type="number"
                    {...capacityForm.register('scrap_quantity', { min: 0 })}
                    className="w-full px-3 py-2 border rounded-lg"
                    step="0.001"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">{t('operator_id') || 'ID Operador'}</label>
                  <input
                    type="text"
                    {...capacityForm.register('operator_id')}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="OPER-001"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">{t('operator_name') || 'Nome Operador'}</label>
                  <input
                    type="text"
                    {...capacityForm.register('operator_name')}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="João Silva"
                  />
                </div>
              </div>
            </form>
          )}
        </div>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            {t('cancel') || 'Cancelar'}
          </button>
          <button
            type="submit"
            form={`${activeTab}-form`}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '⏳ Posting...' : `📝 ${t('post') || 'Registar'}`}
          </button>
        </div>
      </div>
    </div>
  )
}
