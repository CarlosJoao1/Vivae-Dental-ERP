import { useTranslation } from 'react-i18next'

interface Props {
  register: any
  errors?: any
  locations: Array<{ code: string; name: string }>
}

export default function ResourceFields({ register, errors, locations }: Props){
  const { t } = useTranslation()
  return (
    <>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">{t('capacity_min_per_day') || 'Capacity (min/day)'}</label>
          <input type="number" className="input" step="1" {...register('capacity', { min: 0 })} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t('efficiency_pct') || 'Efficiency %'}</label>
          <input type="number" className="input" step="0.1" {...register('efficiency_pct', { min: 0, max: 200 })} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t('unit_cost_per_min') || 'Unit Cost (€/min)'}</label>
          <input type="number" className="input" step="0.01" {...register('unit_cost', { min: 0 })} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-4">
        <div>
          <label className="block text-sm font-medium mb-1">{t('overhead_pct') || 'Overhead %'}</label>
          <input type="number" className="input" step="0.1" {...register('overhead_rate', { min: 0 })} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t('location') as string}</label>
          <select className="input" {...register('location_code')}>
            <option value="">—</option>
            {locations.map((l:any)=> (<option key={l.code} value={l.code}>{l.code} - {l.name}</option>))}
          </select>
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('blocked')} /> {t('blocked') as string}</label>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-4">
        <div>
          <label className="block text-sm font-medium mb-1">{t('queue_time_min') || 'Queue Time (min)'}</label>
          <input type="number" className="input" step="1" {...register('queue_time', { min: 0 })} />
        </div>
      </div>
    </>
  )
}
