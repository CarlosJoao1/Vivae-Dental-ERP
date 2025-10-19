import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">
            {isEdit ? '✏️ Edit UOM' : '➕ Create UOM'}
          </h2>
          <button
            type="button"
            onClick={onCancel}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close form"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
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

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={loading}
            >
              {t('cancel', 'Cancel')}
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              disabled={loading}
            >
              {loading ? '⏳ Saving...' : (isEdit ? '💾 Update' : '➕ Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
