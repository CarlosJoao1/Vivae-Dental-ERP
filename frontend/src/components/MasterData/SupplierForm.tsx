import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

interface SupplierFormData {
  supplier_id: string
  name: string
  contact_name?: string
  email?: string
  phone_no?: string
  address?: string
  city?: string
  postal_code?: string
  country?: string
  lead_time_days_default: number
  currency?: string
  payment_terms?: string
  status: string
}

interface SupplierFormProps {
  supplier?: any
  onSuccess: () => void
  onCancel: () => void
}

export default function SupplierForm({ supplier, onSuccess, onCancel }: SupplierFormProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const isEdit = !!supplier

  const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm<SupplierFormData>({
    defaultValues: {
      supplier_id: supplier?.supplier_id || '',
      name: supplier?.name || '',
      contact_name: supplier?.contact_name || '',
      email: supplier?.email || '',
      phone_no: supplier?.phone_no || '',
      address: supplier?.address || '',
      city: supplier?.city || '',
      postal_code: supplier?.postal_code || '',
      country: supplier?.country || '',
      lead_time_days_default: supplier?.lead_time_days_default || 0,
      currency: supplier?.currency || 'EUR',
      payment_terms: supplier?.payment_terms || '',
      status: supplier?.status || 'Active'
    }
  })

  const onSubmit = async (data: SupplierFormData) => {
    setLoading(true)
    try {
      const endpoint = isEdit 
        ? `/api/production/masterdata/suppliers/${supplier.id}`
        : '/api/production/masterdata/suppliers'
      
      const method = isEdit ? 'PATCH' : 'POST'
      
      await api(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      toast.success(isEdit ? '✅ Supplier updated successfully!' : '✅ Supplier created successfully!')
      onSuccess()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      toast.error(`❌ Failed to save supplier: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">
            {isEdit ? '✏️ Edit Supplier' : '➕ Create Supplier'}
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

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Section: Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              📋 Basic Information
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('supplier_id', 'Supplier ID')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  {...register('supplier_id', { 
                    required: 'Supplier ID is required',
                    pattern: {
                      value: /^[A-Z0-9_-]+$/,
                      message: 'Use uppercase letters, numbers, hyphens and underscores only'
                    }
                  })}
                  disabled={isEdit}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    errors.supplier_id ? 'border-red-500' : 'border-gray-300'
                  } ${isEdit ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                  placeholder="SUP-001"
                />
                {errors.supplier_id && (
                  <p className="text-red-500 text-sm mt-1">{errors.supplier_id.message}</p>
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
                  placeholder="Supplier Company Name"
                />
                {errors.name && (
                  <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
                )}
              </div>
            </div>
          </div>

          {/* Section: Contact Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              📞 Contact Information
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('contact_name', 'Contact Name')}
                </label>
                <input
                  type="text"
                  {...register('contact_name')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('phone_no', 'Phone Number')}
                </label>
                <input
                  type="tel"
                  {...register('phone_no')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="+351 912 345 678"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('email', 'Email')}
              </label>
              <input
                type="email"
                {...register('email', {
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.email ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="supplier@example.com"
              />
              {errors.email && (
                <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
              )}
            </div>
          </div>

          {/* Section: Address */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              📍 Address
            </h3>

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
          </div>

          {/* Section: Business Terms */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-700 border-b pb-2">
              💼 Business Terms
            </h3>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('lead_time_days', 'Lead Time (Days)')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  {...register('lead_time_days_default', { 
                    required: 'Lead time is required',
                    min: { value: 0, message: 'Must be 0 or greater' },
                    valueAsNumber: true
                  })}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    errors.lead_time_days_default ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="7"
                />
                {errors.lead_time_days_default && (
                  <p className="text-red-500 text-sm mt-1">{errors.lead_time_days_default.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('currency', 'Currency')}
                </label>
                <select
                  {...register('currency')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="EUR">EUR (€)</option>
                  <option value="USD">USD ($)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="JPY">JPY (¥)</option>
                  <option value="CHF">CHF</option>
                </select>
              </div>

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
                  <option value="Blocked">🚫 Blocked</option>
                </select>
                {errors.status && (
                  <p className="text-red-500 text-sm mt-1">{errors.status.message}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('payment_terms', 'Payment Terms')}
              </label>
              <input
                type="text"
                {...register('payment_terms')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Net 30 days"
              />
              <p className="text-gray-500 text-xs mt-1">
                💡 Examples: "Net 30 days", "COD", "2/10 Net 30"
              </p>
            </div>
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
