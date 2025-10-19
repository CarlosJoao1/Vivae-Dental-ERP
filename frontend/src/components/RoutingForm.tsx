import { useState, useEffect } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { api } from '@/lib/api'

interface RoutingOperation {
  operation_no: number
  work_center_code: string
  machine_center_code: string
  description: string
  setup_time: number
  run_time: number
  concurrent_capacities: number
}

interface RoutingFormData {
  item_no: string
  version_code: string
  status: string
  operations: RoutingOperation[]
}

interface RoutingFormProps {
  routing?: any
  onSuccess: () => void
  onCancel: () => void
}

export default function RoutingForm({ routing, onSuccess, onCancel }: RoutingFormProps) {
  const { t } = useTranslation()
  const [items, setItems] = useState<any[]>([])
  const [workCenters, setWorkCenters] = useState<any[]>([])
  const [machineCenters, setMachineCenters] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const isEditMode = !!routing
  
  const { register, control, handleSubmit, watch, formState: { errors } } = useForm<RoutingFormData>({
    defaultValues: routing ? {
      item_no: routing.item_no,
      version_code: routing.version_code,
      status: routing.status,
      operations: routing.operations || []
    } : {
      item_no: '',
      version_code: 'V1',
      status: 'New',
      operations: [{ operation_no: 10, work_center_code: '', machine_center_code: '', description: '', setup_time: 0, run_time: 60, concurrent_capacities: 1 }]
    }
  })
  
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'operations'
  })
  
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    try {
      const [itemsRes, wcRes, mcRes] = await Promise.all([
        api<any[]>('/api/production/masterdata/items'),
        api<any[]>('/api/production/work-centers'),
        api<any[]>('/api/production/machine-centers')
      ])
      setItems(itemsRes)
      setWorkCenters(wcRes)
      setMachineCenters(mcRes)
    } catch (err: any) {
      console.error('Failed to load form data:', err)
    }
  }
  
  const onSubmit = async (data: RoutingFormData) => {
    setLoading(true)
    setError('')
    
    try {
      // Validate at least one operation
      if (data.operations.length === 0) {
        setError('At least one operation is required')
        setLoading(false)
        return
      }
      
      // Validate times
      for (const op of data.operations) {
        if (op.setup_time < 0) {
          setError(`Operation ${op.operation_no}: Setup time must be >= 0`)
          setLoading(false)
          return
        }
        if (op.run_time <= 0) {
          setError(`Operation ${op.operation_no}: Run time must be > 0`)
          setLoading(false)
          return
        }
        if (op.concurrent_capacities < 1) {
          setError(`Operation ${op.operation_no}: Concurrent capacities must be >= 1`)
          setLoading(false)
          return
        }
      }
      
      if (isEditMode) {
        // Update existing routing
        await api(`/api/production/routings/${routing.id}`, {
          method: 'PATCH',
          body: JSON.stringify(data)
        })
      } else {
        // Create new routing
        await api('/api/production/routings', {
          method: 'POST',
          body: JSON.stringify(data)
        })
      }
      
      onSuccess()
    } catch (err: any) {
      setError(err.message || 'Failed to save routing')
      setLoading(false)
    }
  }
  
  const addOperation = () => {
    const lastOpNo = fields.length > 0 ? fields[fields.length - 1].operation_no : 0
    append({
      operation_no: lastOpNo + 10,
      work_center_code: '',
      machine_center_code: '',
      description: '',
      setup_time: 0,
      run_time: 60,
      concurrent_capacities: 1
    })
  }
  
  const getMachinesForWC = (wcCode: string) => {
    return machineCenters.filter(mc => mc.work_center_code === wcCode)
  }
  
  // Get manufactured items
  const manufacturedItems = items.filter(i => i.item_type === 'manufactured' || i.item_type === 'semi-finished')
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">
            {isEditMode ? `📝 ${t('edit_routing') || 'Edit Routing'}` : `➕ ${t('create_routing') || 'Create Routing'}`}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {t('routing_form_desc') || 'Define operations sequence for manufacturing'}
          </p>
        </div>
        
        {/* Form Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <form id="routing-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Error Banner */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                ❌ {error}
              </div>
            )}
            
            {/* Header Fields */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('item_no') || 'Item No'} <span className="text-red-600">*</span>
                </label>
                <select
                  {...register('item_no', { required: 'Item is required' })}
                  disabled={isEditMode}
                  className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100"
                >
                  <option value="">{t('select') || 'Select...'}</option>
                  {manufacturedItems.map(item => (
                    <option key={item.item_no} value={item.item_no}>
                      {item.item_no} - {item.description}
                    </option>
                  ))}
                </select>
                {errors.item_no && (
                  <p className="text-xs text-red-600 mt-1">{errors.item_no.message}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('version_code') || 'Version'} <span className="text-red-600">*</span>
                </label>
                <input
                  type="text"
                  {...register('version_code', { required: 'Version is required' })}
                  disabled={isEditMode}
                  className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100"
                  placeholder="V1"
                />
                {errors.version_code && (
                  <p className="text-xs text-red-600 mt-1">{errors.version_code.message}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('status') || 'Status'}
                </label>
                <select
                  {...register('status')}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="New">{t('new') || 'New'}</option>
                  <option value="Under Development">{t('under_development') || 'Under Development'}</option>
                  <option value="Certified">{t('certified') || 'Certified'}</option>
                  <option value="Closed">{t('closed') || 'Closed'}</option>
                </select>
              </div>
            </div>
            
            {/* Operations */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">{t('operations') || 'Operations'}</h3>
                <button
                  type="button"
                  onClick={addOperation}
                  className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                >
                  ➕ {t('add_operation') || 'Add Operation'}
                </button>
              </div>
              
              <div className="space-y-3">
                {fields.map((field: any, index: number) => {
                  const selectedWC = watch(`operations.${index}.work_center_code`)
                  const filteredMachines = getMachinesForWC(selectedWC)
                  
                  return (
                    <div key={field.id} className="border rounded-lg p-4 bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-3">
                        <div>
                          <label className="block text-xs font-medium mb-1">{t('op_no') || 'Op No'}</label>
                          <input
                            type="number"
                            {...register(`operations.${index}.operation_no` as const)}
                            className="w-full px-2 py-1 border rounded text-sm"
                            step="10"
                          />
                        </div>
                        
                        <div className="md:col-span-2">
                          <label className="block text-xs font-medium mb-1">
                            {t('work_center') || 'Work Center'} <span className="text-red-600">*</span>
                          </label>
                          <select
                            {...register(`operations.${index}.work_center_code` as const, { required: true })}
                            className="w-full px-2 py-1 border rounded text-sm"
                          >
                            <option value="">Select...</option>
                            {workCenters.map(wc => (
                              <option key={wc.code} value={wc.code}>
                                {wc.code} - {wc.name}
                              </option>
                            ))}
                          </select>
                        </div>
                        
                        <div className="md:col-span-2">
                          <label className="block text-xs font-medium mb-1">{t('machine') || 'Machine'}</label>
                          <select
                            {...register(`operations.${index}.machine_center_code` as const)}
                            className="w-full px-2 py-1 border rounded text-sm"
                            disabled={!selectedWC}
                          >
                            <option value="">{t('optional') || 'Optional'}</option>
                            {filteredMachines.map(mc => (
                              <option key={mc.code} value={mc.code}>
                                {mc.code} - {mc.name}
                              </option>
                            ))}
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-xs font-medium mb-1">{t('setup_min') || 'Setup (min)'}</label>
                          <input
                            type="number"
                            {...register(`operations.${index}.setup_time` as const, { min: 0 })}
                            className="w-full px-2 py-1 border rounded text-sm"
                            step="1"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs font-medium mb-1">
                            {t('run_min') || 'Run (min)'} <span className="text-red-600">*</span>
                          </label>
                          <input
                            type="number"
                            {...register(`operations.${index}.run_time` as const, { required: true, min: 0.1 })}
                            className="w-full px-2 py-1 border rounded text-sm"
                            step="0.1"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
                        <div className="md:col-span-2">
                          <label className="block text-xs font-medium mb-1">{t('description') || 'Description'}</label>
                          <input
                            type="text"
                            {...register(`operations.${index}.description` as const)}
                            className="w-full px-2 py-1 border rounded text-sm"
                            placeholder="Optional operation description"
                          />
                        </div>
                        
                        <div className="flex items-end gap-2">
                          <div className="flex-1">
                            <label className="block text-xs font-medium mb-1">{t('concurrent') || 'Concurrent'}</label>
                            <input
                              type="number"
                              {...register(`operations.${index}.concurrent_capacities` as const, { min: 1 })}
                              className="w-full px-2 py-1 border rounded text-sm"
                              step="1"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => remove(index)}
                            disabled={fields.length === 1}
                            className="px-3 py-1 text-red-600 hover:text-red-800 disabled:text-gray-400 disabled:cursor-not-allowed border rounded"
                            title={t('remove_operation') || 'Remove'}
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
              
              {fields.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  {t('no_operations') || 'No operations added. Click "Add Operation" to start.'}
                </p>
              )}
            </div>
          </form>
        </div>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            {t('cancel') || 'Cancel'}
          </button>
          <button
            type="submit"
            form="routing-form"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '⏳ Saving...' : (isEditMode ? '💾 Update' : '➕ Create')}
          </button>
        </div>
      </div>
    </div>
  )
}
