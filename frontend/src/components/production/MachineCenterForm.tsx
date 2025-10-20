import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { useTranslation } from 'react-i18next'
import { api } from '@/lib/api'
import FormModal from '@/components/common/FormModal'
import ErrorBoundary from '@/components/common/ErrorBoundary'

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
    try { const wcs = await api<any>('/api/production/work-centers'); setWorkCenters(wcs.items||[]) } catch {}
    try { const locs = await api<any[]>('/api/production/masterdata/locations'); setLocations(locs) } catch {}
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
        title="Machine Center"
        onClose={onCancel}
        onSubmit={handleSubmit(onSubmit)}
        loading={loading}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Code *</label>
              <input className="input" {...register('code', { required: 'Required', pattern: { value: /^[A-Z0-9_-]+$/, message: 'Use A-Z, 0-9, -, _' } })} />
              {errors.code && <p className="text-xs text-red-600 mt-1">{errors.code.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Name *</label>
              <input className="input" {...register('name', { required: 'Required' })} />
              {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name.message}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Work Center *</label>
              <select className="input" {...register('work_center_code', { required: 'Required' })}>
                <option value="">Select...</option>
                {workCenters.map((wc:any)=> (<option key={wc.id} value={wc.code}>{wc.code} - {wc.name}</option>))}
              </select>
              {errors.work_center_code && <p className="text-xs text-red-600 mt-1">{errors.work_center_code.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Location</label>
              <select className="input" {...register('location_code')}>
                <option value="">—</option>
                {locations.map((l:any)=> (<option key={l.code} value={l.code}>{l.code} - {l.name}</option>))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Capacity (min/day)</label>
              <input type="number" className="input" step="1" {...register('capacity', { min: 0 })} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Efficiency %</label>
              <input type="number" className="input" step="0.1" {...register('efficiency_pct', { min: 0, max: 200 })} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Unit Cost (€/min)</label>
              <input type="number" className="input" step="0.01" {...register('unit_cost', { min: 0 })} />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Overhead %</label>
              <input type="number" className="input" step="0.1" {...register('overhead_rate', { min: 0 })} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Queue Time (min)</label>
              <input type="number" className="input" step="1" {...register('queue_time', { min: 0 })} />
            </div>
            <label className="flex items-center gap-2 text-sm mt-6"><input type="checkbox" {...register('blocked')} /> Blocked</label>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Manufacturer</label>
              <input className="input" {...register('manufacturer')} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Model</label>
              <input className="input" {...register('model')} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Serial</label>
              <input className="input" {...register('serial_number')} />
            </div>
          </div>
        </div>
      </FormModal>
    </ErrorBoundary>
  )
}
