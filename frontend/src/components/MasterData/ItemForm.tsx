import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'
import FormModal from '@/components/common/FormModal'

interface ItemFormData {
  item_no: string
  description: string
  description_2?: string
  item_type: 'manufactured' | 'purchased' | 'both'
  base_uom: string
  lead_time_days: number
  unit_cost?: number
  status: string
}

interface ItemFormProps {
  item?: any
  onSuccess: () => void
  onCancel: () => void
}

export default function ItemForm({ item, onSuccess, onCancel }: ItemFormProps) {
  const { t } = useTranslation()
  const [uoms, setUOMs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const isEdit = !!item

  const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm<ItemFormData>({
    defaultValues: {
      item_no: item?.item_no || '',
      description: item?.description || '',
      description_2: item?.description_2 || '',
      item_type: item?.item_type || 'manufactured',
      base_uom: item?.base_uom || 'PCS',
      lead_time_days: item?.lead_time_days || 0,
      unit_cost: item?.unit_cost || 0,
      status: item?.status || 'Active'
    }
  })

  useEffect(() => {
    loadUOMs()
  }, [])

  const loadUOMs = async () => {
    try {
      const response = await api<any>('/api/production/masterdata/uom')
      setUOMs(response.items || [])
    } catch (err) {
      toast.error('Failed to load UOMs')
    }
  }

  const onSubmit = async (data: ItemFormData) => {
    setLoading(true)
    try {
      const endpoint = isEdit 
        ? `/api/production/masterdata/items/${item.id}`
        : '/api/production/masterdata/items'
      
      const method = isEdit ? 'PATCH' : 'POST'
      
      await api(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      toast.success(isEdit ? '✅ Item updated successfully!' : '✅ Item created successfully!')
      onSuccess()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      toast.error(`❌ Failed to save item: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormModal
      isOpen={true}
      title="Item"
      onClose={onCancel}
      onSubmit={handleSubmit(onSubmit)}
      loading={loading}
      isEdit={isEdit}
    >
      <div className="space-y-4">
          {/* Item Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('item_no', 'Item No.')} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('item_no', { 
                required: 'Item number is required',
                pattern: {
                  value: /^[A-Z0-9_-]+$/,
                  message: 'Use uppercase letters, numbers, hyphens and underscores only'
                }
              })}
              disabled={isEdit}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.item_no ? 'border-red-500' : 'border-gray-300'
              } ${isEdit ? 'bg-gray-100 cursor-not-allowed' : ''}`}
              placeholder="ITEM-001"
            />
            {errors.item_no && (
              <p className="text-red-500 text-sm mt-1">{errors.item_no.message}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('description', 'Description')} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('description', { required: 'Description is required' })}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.description ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Item description"
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
            )}
          </div>

          {/* Description 2 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('description_2', 'Description 2')}
            </label>
            <input
              type="text"
              {...register('description_2')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Additional description (optional)"
            />
          </div>

          {/* Item Type and Base UOM (2 columns) */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('item_type', 'Item Type')} <span className="text-red-500">*</span>
              </label>
              <select
                {...register('item_type', { required: 'Item type is required' })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.item_type ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="manufactured">🏭 Manufactured</option>
                <option value="purchased">🛒 Purchased</option>
                <option value="both">🔄 Both</option>
              </select>
              {errors.item_type && (
                <p className="text-red-500 text-sm mt-1">{errors.item_type.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('base_uom', 'Base UOM')} <span className="text-red-500">*</span>
              </label>
              <select
                {...register('base_uom', { required: 'Base UOM is required' })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.base_uom ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                {uoms.length === 0 && <option value="PCS">PCS</option>}
                {uoms.map(uom => (
                  <option key={uom.id} value={uom.code}>
                    {uom.code} - {uom.description}
                  </option>
                ))}
              </select>
              {errors.base_uom && (
                <p className="text-red-500 text-sm mt-1">{errors.base_uom.message}</p>
              )}
            </div>
          </div>

          {/* Lead Time and Unit Cost (2 columns) */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('lead_time_days', 'Lead Time (Days)')} <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                {...register('lead_time_days', { 
                  required: 'Lead time is required',
                  min: { value: 0, message: 'Must be 0 or greater' },
                  valueAsNumber: true
                })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.lead_time_days ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="0"
              />
              {errors.lead_time_days && (
                <p className="text-red-500 text-sm mt-1">{errors.lead_time_days.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('unit_cost', 'Unit Cost')}
              </label>
              <input
                type="number"
                step="0.01"
                {...register('unit_cost', { 
                  min: { value: 0, message: 'Must be 0 or greater' },
                  valueAsNumber: true
                })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.unit_cost ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="0.00"
              />
              {errors.unit_cost && (
                <p className="text-red-500 text-sm mt-1">{errors.unit_cost.message}</p>
              )}
            </div>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('status', 'Status')} <span className="text-red-500">*</span>
            </label>
            <select
              {...register('status', { required: 'Status is required' })}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.status ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="Active">✅ Active</option>
              <option value="Inactive">⏸️ Inactive</option>
              <option value="Obsolete">❌ Obsolete</option>
            </select>
            {errors.status && (
              <p className="text-red-500 text-sm mt-1">{errors.status.message}</p>
            )}
          </div>
        </div>
      </FormModal>
  )
}
