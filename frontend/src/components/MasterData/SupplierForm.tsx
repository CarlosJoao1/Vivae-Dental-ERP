import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'
import FormModal from '@/components/common/FormModal'
import ErrorBoundary from '@/components/common/ErrorBoundary'

interface SupplierFormData {
  code: string
  name: string
  contact_person?: string
  email?: string
  phone?: string
  address?: string
  city?: string
  postal_code?: string
  country?: string
  payment_terms?: string
  currency?: string
  tax_id?: string
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
      code: supplier?.code || '',
      name: supplier?.name || '',
      contact_person: supplier?.contact_person || '',
      email: supplier?.email || '',
      phone: supplier?.phone || '',
      address: supplier?.address || '',
      city: supplier?.city || '',
      postal_code: supplier?.postal_code || '',
      country: supplier?.country || '',
      payment_terms: supplier?.payment_terms || '',
      currency: supplier?.currency || 'EUR',
      tax_id: supplier?.tax_id || ''
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
    <ErrorBoundary context="SupplierForm">
    <FormModal
      isOpen={true}
      title="Supplier"
      onClose={onCancel}
      onSubmit={handleSubmit(onSubmit)}
      loading={loading}
      isEdit={isEdit}
    >
      <div className="space-y-6">
        {/* Basic Information */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            📋 Basic Information
          </h4>
          <div className="space-y-4">
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
                  placeholder="SUPP-001"
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
                  placeholder="Supplier Name Ltd."
                />
                {errors.name && (
                  <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            📞 Contact Information
          </h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('contact_person', 'Contact Person')}
              </label>
              <input
                type="text"
                {...register('contact_person')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="John Doe"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
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
                  placeholder="contact@supplier.com"
                />
                {errors.email && (
                  <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('phone', 'Phone')}
                </label>
                <input
                  type="tel"
                  {...register('phone')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="+351 123 456 789"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Address Information */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            📍 Address Information
          </h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('address', 'Address')}
              </label>
              <input
                type="text"
                {...register('address')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="123 Business Street"
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
        </div>

        {/* Business Terms */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
            💼 Business Terms
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('payment_terms', 'Payment Terms')}
              </label>
              <input
                type="text"
                {...register('payment_terms')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Net 30"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('currency', 'Currency')}
              </label>
              <select
                {...register('currency')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="EUR">💶 EUR - Euro</option>
                <option value="USD">💵 USD - US Dollar</option>
                <option value="GBP">💷 GBP - British Pound</option>
                <option value="JPY">💴 JPY - Japanese Yen</option>
                <option value="CNY">💴 CNY - Chinese Yuan</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('tax_id', 'Tax ID / VAT')}
              </label>
              <input
                type="text"
                {...register('tax_id')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="PT123456789"
              />
            </div>
          </div>
        </div>
      </div>
    </FormModal>
    </ErrorBoundary>
  )
}
