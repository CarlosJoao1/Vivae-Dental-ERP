import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { useTranslation } from 'react-i18next'
import { api } from '@/lib/api'
import FormModal from '@/components/common/FormModal'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import ResourceFields from '@/components/production/ResourceFields'

interface MachineCenterFormData {
  code: string
  name: string
  description?: string
  work_center_code: string
  capacity?: number
  efficiency_pct?: number
  unit_cost?: number
  overhead_rate?: number
  location_code?: string
  blocked?: boolean
  queue_time?: number
  manufacturer?: string
  model?: string
  serial_number?: string
}

interface MachineCenterFormProps {
  onSuccess: () => void
  onCancel: () => void
}

export default function MachineCenterForm({ onSuccess, onCancel }: MachineCenterFormProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [workCenters, setWorkCenters] = useState<any[]>([])
  const [locations, setLocations] = useState<any[]>([])

  useEffect(() => { (async () => {
    try {
      const wcs = await api<any>('/api/production/work-centers')
      setWorkCenters(Array.isArray(wcs) ? wcs : (wcs?.items || []))
    } catch(e){ console.warn('Failed to load work centers', e); setWorkCenters([]) }
    try {
      const locs = await api<any>('/api/production/masterdata/locations')
      setLocations(Array.isArray(locs) ? locs : (locs?.items || []))
    } catch(e){ console.warn('Failed to load locations', e); setLocations([]) }
  })() }, [])

  const { register, handleSubmit, formState: { errors } } = useForm<MachineCenterFormData>({
    defaultValues: {
      capacity: 480,
      efficiency_pct: 100,
      unit_cost: 0,
      overhead_rate: 0,
      blocked: false,
      queue_time: 0,
    }
  })

  const onSubmit = async (data: MachineCenterFormData) => {
    setLoading(true)
    try {
      await api('/api/production/machine-centers', { method: 'POST', body: JSON.stringify(data) })
      toast.success('✅ Machine Center created successfully')
      onSuccess()
    } catch (e:any) {
      toast.error(e?.message || 'Failed to create Machine Center')
      setLoading(false)
    }
  }

  return (
    <ErrorBoundary context="MachineCenterForm">
      <FormModal
        isOpen={true}
        title={t('machine_center') || 'Machine Center'}
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('work_center') as string} *</label>
              <select className="input" {...register('work_center_code', { required: 'Required' })}>
                <option value="">Select...</option>
                {workCenters.map((wc:any)=> (<option key={wc.id} value={wc.code}>{wc.code} - {wc.name}</option>))}
              </select>
              {errors.work_center_code && <p className="text-xs text-red-600 mt-1">{errors.work_center_code.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('location') as string}</label>
              <select className="input" {...register('location_code')}>
                <option value="">—</option>
                {locations.map((l:any)=> (<option key={l.code} value={l.code}>{l.code} - {l.name}</option>))}
              </select>
            </div>
          </div>

          <ResourceFields register={register} errors={errors} locations={locations} />

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('manufacturer') || 'Manufacturer'}</label>
              <input className="input" {...register('manufacturer')} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('model') || 'Model'}</label>
              <input className="input" {...register('model')} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('serial_number') || 'Serial'}</label>
              <input className="input" {...register('serial_number')} />
            </div>
          </div>
        </div>
      </FormModal>
    </ErrorBoundary>
  )
}
