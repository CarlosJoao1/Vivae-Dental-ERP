import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { api } from '@/lib/api'

interface ProductionOrderFormData {
  item_no: string
  quantity: number
  uom_code: string
  due_date: string
  bom_version_code: string
  routing_version_code: string
}

interface ProductionOrderFormProps {
  onSuccess: () => void
  onCancel: () => void
}

export default function ProductionOrderForm({ onSuccess, onCancel }: ProductionOrderFormProps) {
  const { t } = useTranslation()
  const [items, setItems] = useState<any[]>([])
  const [boms, setBOMs] = useState<any[]>([])
  const [routings, setRoutings] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedItem, setSelectedItem] = useState<any>(null)
  
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<ProductionOrderFormData>({
    defaultValues: {
      item_no: '',
      quantity: 1,
      uom_code: 'UN',
      due_date: new Date().toISOString().split('T')[0],
      bom_version_code: '',
      routing_version_code: ''
    }
  })
  
  const watchedItemNo = watch('item_no')
  
  useEffect(() => {
    loadItems()
  }, [])
  
  useEffect(() => {
    if (watchedItemNo) {
      loadBOMsAndRoutings(watchedItemNo)
    }
  }, [watchedItemNo])
  
  const loadItems = async () => {
    try {
      const itemsRes = await api<any[]>('/api/production/masterdata/items')
      setItems(itemsRes)
    } catch (err: any) {
      console.error('Failed to load items:', err)
    }
  }
  
  const loadBOMsAndRoutings = async (itemNo: string) => {
    try {
      const item = items.find(i => i.item_no === itemNo)
      setSelectedItem(item)
      
      // Auto-fill UOM
      if (item?.base_uom) {
        setValue('uom_code', item.base_uom)
      }
      
      // Load BOMs and Routings for this item
      const [bomsRes, routingsRes] = await Promise.all([
        api<any[]>('/api/production/boms'),
        api<any[]>('/api/production/routings')
      ])
      
      const itemBOMs = bomsRes.filter(b => b.item_no === itemNo)
      const itemRoutings = routingsRes.filter(r => r.item_no === itemNo)
      
      setBOMs(itemBOMs)
      setRoutings(itemRoutings)
      
      // Auto-select certified versions
      const certifiedBOM = itemBOMs.find(b => b.status === 'Certified')
      const certifiedRouting = itemRoutings.find(r => r.status === 'Certified')
      
      if (certifiedBOM) {
        setValue('bom_version_code', certifiedBOM.version_code)
      } else if (itemBOMs.length > 0) {
        setValue('bom_version_code', itemBOMs[0].version_code)
      }
      
      if (certifiedRouting) {
        setValue('routing_version_code', certifiedRouting.version_code)
      } else if (itemRoutings.length > 0) {
        setValue('routing_version_code', itemRoutings[0].version_code)
      }
    } catch (err: any) {
      console.error('Failed to load BOMs/Routings:', err)
    }
  }
  
  const onSubmit = async (data: ProductionOrderFormData) => {
    setLoading(true)
    setError('')
    
    try {
      // Validate quantity
      if (data.quantity <= 0) {
        setError('Quantity must be > 0')
        setLoading(false)
        return
      }
      
      // Check BOM exists
      if (!data.bom_version_code) {
        setError('BOM version is required. Please create a BOM for this item first.')
        setLoading(false)
        return
      }
      
      // Check Routing exists
      if (!data.routing_version_code) {
        setError('Routing version is required. Please create a Routing for this item first.')
        setLoading(false)
        return
      }
      
      // Create production order
      await api('/api/production/production-orders', {
        method: 'POST',
        body: JSON.stringify(data)
      })
      
      onSuccess()
    } catch (err: any) {
      setError(err.message || 'Failed to create production order')
      setLoading(false)
    }
  }
  
  // Get manufactured items
  const manufacturedItems = items.filter(i => i.item_type === 'manufactured' || i.item_type === 'semi-finished')
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">
            ➕ {t('create_production_order') || 'Create Production Order'}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {t('production_order_form_desc') || 'Create a new production order for a manufactured item'}
          </p>
        </div>
        
        {/* Form Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <form id="production-order-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Error Banner */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                ❌ {error}
              </div>
            )}
            
            {/* Item Selection */}
            <div>
              <label className="block text-sm font-medium mb-1">
                {t('item_no') || 'Item No'} <span className="text-red-600">*</span>
              </label>
              <select
                {...register('item_no', { required: 'Item is required' })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">{t('select_item') || 'Select an item...'}</option>
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
            
            {selectedItem && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  📦 <strong>{selectedItem.description}</strong>
                  <br />
                  <span className="text-xs">
                    Type: {selectedItem.item_type} | Base UOM: {selectedItem.base_uom}
                  </span>
                </p>
              </div>
            )}
            
            {/* Quantity and UOM */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('quantity') || 'Quantity'} <span className="text-red-600">*</span>
                </label>
                <input
                  type="number"
                  {...register('quantity', { required: 'Quantity is required', min: 0.001 })}
                  className="w-full px-3 py-2 border rounded-lg"
                  step="0.001"
                />
                {errors.quantity && (
                  <p className="text-xs text-red-600 mt-1">{errors.quantity.message}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('uom') || 'UOM'}
                </label>
                <input
                  type="text"
                  {...register('uom_code')}
                  className="w-full px-3 py-2 border rounded-lg bg-gray-50"
                  readOnly
                />
              </div>
            </div>
            
            {/* Due Date */}
            <div>
              <label className="block text-sm font-medium mb-1">
                {t('due_date') || 'Due Date'} <span className="text-red-600">*</span>
              </label>
              <input
                type="date"
                {...register('due_date', { required: 'Due date is required' })}
                className="w-full px-3 py-2 border rounded-lg"
              />
              {errors.due_date && (
                <p className="text-xs text-red-600 mt-1">{errors.due_date.message}</p>
              )}
            </div>
            
            {/* BOM Version */}
            <div>
              <label className="block text-sm font-medium mb-1">
                {t('bom_version') || 'BOM Version'} <span className="text-red-600">*</span>
              </label>
              <select
                {...register('bom_version_code', { required: 'BOM version is required' })}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={!watchedItemNo || boms.length === 0}
              >
                <option value="">
                  {watchedItemNo ? (boms.length > 0 ? 'Select version...' : 'No BOMs available') : 'Select item first'}
                </option>
                {boms.map(bom => (
                  <option key={bom.id} value={bom.version_code}>
                    {bom.version_code} - {bom.status} ({bom.lines?.length || 0} lines)
                  </option>
                ))}
              </select>
              {errors.bom_version_code && (
                <p className="text-xs text-red-600 mt-1">{errors.bom_version_code.message}</p>
              )}
              {boms.length === 0 && watchedItemNo && (
                <p className="text-xs text-yellow-600 mt-1">
                  ⚠️ No BOM found for this item. Please create one first.
                </p>
              )}
            </div>
            
            {/* Routing Version */}
            <div>
              <label className="block text-sm font-medium mb-1">
                {t('routing_version') || 'Routing Version'} <span className="text-red-600">*</span>
              </label>
              <select
                {...register('routing_version_code', { required: 'Routing version is required' })}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={!watchedItemNo || routings.length === 0}
              >
                <option value="">
                  {watchedItemNo ? (routings.length > 0 ? 'Select version...' : 'No Routings available') : 'Select item first'}
                </option>
                {routings.map(routing => (
                  <option key={routing.id} value={routing.version_code}>
                    {routing.version_code} - {routing.status} ({routing.operations?.length || 0} ops)
                  </option>
                ))}
              </select>
              {errors.routing_version_code && (
                <p className="text-xs text-red-600 mt-1">{errors.routing_version_code.message}</p>
              )}
              {routings.length === 0 && watchedItemNo && (
                <p className="text-xs text-yellow-600 mt-1">
                  ⚠️ No Routing found for this item. Please create one first.
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
            form="production-order-form"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '⏳ Creating...' : '➕ Create Order'}
          </button>
        </div>
      </div>
    </div>
  )
}
