import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { useTranslation } from 'react-i18next'
import { api } from '@/lib/api'
import FormModal from '@/components/common/FormModal'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import ResourceFields from '@/components/production/ResourceFields'

interface WorkCenterFormData {
  code: string
  name: string
  description?: string
  work_center_type?: 'Work Center' | 'Machine Center' | 'Person'
  capacity?: number
  efficiency_pct?: number
  calendar_code?: string
  unit_cost?: number
  overhead_rate?: number
  location_code?: string
  blocked?: boolean
  queue_time?: number
}

interface WorkCenterFormProps {
  onSuccess: () => void
  onCancel: () => void
}

export default function WorkCenterForm({ onSuccess, onCancel }: WorkCenterFormProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [locations, setLocations] = useState<any[]>([])

  useEffect(() => { (async () => {
    try {
      const locs = await api<any[]>('/api/production/masterdata/locations'); setLocations(locs)
    } catch(e){ console.warn('Failed to load locations', e); setLocations([]) }
  })() }, [])

  const { register, handleSubmit, formState: { errors } } = useForm<WorkCenterFormData>({
    defaultValues: {
      work_center_type: 'Work Center',
      capacity: 480,
      efficiency_pct: 100,
      unit_cost: 0,
      overhead_rate: 0,
      blocked: false,
      queue_time: 0,
    }
  })

  const onSubmit = async (data: WorkCenterFormData) => {
    setLoading(true)
    try {
      await api('/api/production/work-centers', {
        method: 'POST',
        body: JSON.stringify(data)
      })
      toast.success('✅ Work Center created successfully')
      onSuccess()
    } catch (e:any) {
      toast.error(e?.message || 'Failed to create Work Center')
      setLoading(false)
    }
  }

  return (
    <ErrorBoundary context="WorkCenterForm">
      <FormModal
        isOpen={true}
        title={t('work_center') || 'Work Center'}
        onClose={onCancel}
        onSubmit={handleSubmit(onSubmit)}
        loading={loading}
        cancelLabel={t('cancel') as string}
        submitLabel={t('create') as string}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('code') as string} *</label>
              <input className="input" {...register('code', { required: String(t('required')||'Required'), pattern: { value: /^[A-Z0-9_-]+$/, message: String(t('code_pattern_hint')||'Use A-Z, 0-9, -, _') } })} />
              {errors.code && <p className="text-xs text-red-600 mt-1">{errors.code.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('name') as string} *</label>
              <input className="input" {...register('name', { required: String(t('required')||'Required') })} />
              {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name.message}</p>}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('description') as string}</label>
            <input className="input" {...register('description')} />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('type') as string}</label>
              <select className="input" {...register('work_center_type')}>
                <option value="Work Center">{t('work_center') || 'Work Center'}</option>
                <option value="Machine Center">{t('machine_center') || 'Machine Center'}</option>
                <option value="Person">{t('person') || 'Person'}</option>
              </select>
            </div>
          </div>

          <ResourceFields register={register} errors={errors} locations={locations} />
        </div>
      </FormModal>
    </ErrorBoundary>
  )
}
