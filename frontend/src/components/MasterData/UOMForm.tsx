import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'
import FormModal from '@/components/common/FormModal'

interface UOMFormData {
  code: string
  description: string
  decimals: number
}

interface UOMFormProps {
  uom?: any
  onSuccess: () => void
  onCancel: () => void
}

export default function UOMForm({ uom, onSuccess, onCancel }: UOMFormProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const isEdit = !!uom

  const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm<UOMFormData>({
    defaultValues: {
      code: uom?.code || '',
      description: uom?.description || '',
      decimals: uom?.decimals || 0
    }
  })

  const onSubmit = async (data: UOMFormData) => {
    setLoading(true)
    try {
      const endpoint = isEdit 
        ? `/api/production/masterdata/uom/${uom.id}`
        : '/api/production/masterdata/uom'
      
      const method = isEdit ? 'PATCH' : 'POST'
      
      await api(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      toast.success(isEdit ? '✅ UOM updated successfully!' : '✅ UOM created successfully!')
      onSuccess()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      toast.error(`❌ Failed to save UOM: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormModal
      isOpen={true}
      title="Unit of Measure"
      onClose={onCancel}
      onSubmit={handleSubmit(onSubmit)}
      loading={loading}
      isEdit={isEdit}
    >
      <div className="space-y-4">
          {/* Code */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('code', 'Code')} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('code', { 
                required: 'Code is required',
                pattern: {
                  value: /^[A-Z0-9]+$/,
                  message: 'Use uppercase letters and numbers only'
                },
                maxLength: {
                  value: 10,
                  message: 'Maximum 10 characters'
                }
              })}
              disabled={isEdit}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.code ? 'border-red-500' : 'border-gray-300'
              } ${isEdit ? 'bg-gray-100 cursor-not-allowed' : ''}`}
              placeholder="PCS"
            />
            {errors.code && (
              <p className="text-red-500 text-sm mt-1">{errors.code.message}</p>
            )}
            {!isEdit && (
              <p className="text-gray-500 text-xs mt-1">
                💡 Examples: PCS (Pieces), KG (Kilograms), M (Meters)
              </p>
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
              placeholder="Pieces"
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
            )}
          </div>

          {/* Decimals */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('decimals', 'Decimal Places')} <span className="text-red-500">*</span>
            </label>
            <select
              {...register('decimals', { 
                required: 'Decimal places is required',
                valueAsNumber: true
              })}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.decimals ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value={0}>0 (whole numbers only)</option>
              <option value={1}>1 (e.g., 10.5)</option>
              <option value={2}>2 (e.g., 10.50)</option>
              <option value={3}>3 (e.g., 10.500)</option>
              <option value={4}>4 (e.g., 10.5000)</option>
            </select>
            {errors.decimals && (
              <p className="text-red-500 text-sm mt-1">{errors.decimals.message}</p>
            )}
            <p className="text-gray-500 text-xs mt-1">
              💡 Controls quantity precision for this unit
            </p>
          </div>
        </div>
      </FormModal>
  )
}
