import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'
import FormModal from '@/components/common/FormModal'

interface LocationFormData {
  code: string
  name: string
  address?: string
  city?: string
  postal_code?: string
  country?: string
  is_default: boolean
  blocked: boolean
}

interface LocationFormProps {
  location?: any
  onSuccess: () => void
  onCancel: () => void
}

export default function LocationForm({ location, onSuccess, onCancel }: LocationFormProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const isEdit = !!location

  const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm<LocationFormData>({
    defaultValues: {
      code: location?.code || '',
      name: location?.name || '',
      address: location?.address || '',
      city: location?.city || '',
      postal_code: location?.postal_code || '',
      country: location?.country || '',
      is_default: location?.is_default || false,
      blocked: location?.blocked || false
    }
  })

  const onSubmit = async (data: LocationFormData) => {
    setLoading(true)
    try {
      const endpoint = isEdit 
        ? `/api/production/masterdata/locations/${location.id}`
        : '/api/production/masterdata/locations'
      
      const method = isEdit ? 'PATCH' : 'POST'
      
      await api(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      toast.success(isEdit ? '✅ Location updated successfully!' : '✅ Location created successfully!')
      onSuccess()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      toast.error(`❌ Failed to save location: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormModal
      isOpen={true}
      title="Location"
      onClose={onCancel}
      onSubmit={handleSubmit(onSubmit)}
      loading={loading}
      isEdit={isEdit}
    >
      <div className="space-y-4">
        {/* Code and Name (2 columns) */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('code', 'Code')} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('code', { 
                required: 'Code is required',
                pattern: {
                  value: /^[A-Z0-9_-]+$/,
                  message: 'Use uppercase letters, numbers, hyphens and underscores only'
                },
                maxLength: {
                  value: 20,
                  message: 'Maximum 20 characters'
                }
              })}
              disabled={isEdit}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.code ? 'border-red-500' : 'border-gray-300'
              } ${isEdit ? 'bg-gray-100 cursor-not-allowed' : ''}`}
              placeholder="MAIN"
            />
            {errors.code && (
              <p className="text-red-500 text-sm mt-1">{errors.code.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('name', 'Name')} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('name', { required: 'Name is required' })}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Main Warehouse"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>
        </div>

        {/* Address */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('address', 'Address')}
          </label>
          <input
            type="text"
            {...register('address')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="123 Main Street"
          />
        </div>

        {/* City, Postal Code, Country (3 columns) */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('city', 'City')}
            </label>
            <input
              type="text"
              {...register('city')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Lisbon"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('postal_code', 'Postal Code')}
            </label>
            <input
              type="text"
              {...register('postal_code')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="1000-001"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('country', 'Country')}
            </label>
            <input
              type="text"
              {...register('country')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Portugal"
            />
          </div>
        </div>

        {/* Checkboxes */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_default"
              {...register('is_default')}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="is_default" className="ml-2 text-sm text-gray-700">
              ⭐ {t('is_default', 'Set as default location')}
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="blocked"
              {...register('blocked')}
              className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
            />
            <label htmlFor="blocked" className="ml-2 text-sm text-gray-700">
              🚫 {t('blocked', 'Block this location (prevent new transactions)')}
            </label>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            💡 <strong>Tip:</strong> Default locations are automatically selected when creating new production orders. 
            Blocked locations cannot be used for new transactions but existing data remains accessible.
          </p>
        </div>
      </div>
    </FormModal>
  )
}
