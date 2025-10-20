import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

interface NumberInputDialogProps {
  isOpen: boolean
  title: string
  message?: string
  initialValue?: number
  min?: number
  max?: number
  step?: number
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: (value: number) => void
  onCancel: () => void
}

export default function NumberInputDialog({
  isOpen,
  title,
  message,
  initialValue = 10,
  min = 0.001,
  max,
  step = 1,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
}: NumberInputDialogProps){
  const { t } = useTranslation()
  const [value, setValue] = useState<number>(initialValue)
  const [err, setErr] = useState<string>('')

  useEffect(()=>{ setValue(initialValue); setErr('') }, [initialValue, isOpen])

  if (!isOpen) return null

  const _confirm = confirmLabel ?? String(t('confirm') || 'Confirm')
  const _cancel = cancelLabel ?? String(t('cancel') || 'Cancel')

  const validate = (n: number) => {
    if (!Number.isFinite(n)) return String(t('invalid_number') || 'Invalid number')
    if (n < min) return String(t('value_too_small') || 'Value is too small')
    if (typeof max === 'number' && n > max) return String(t('value_too_large') || 'Value is too large')
    return ''
  }

  const onOk = () => {
    const e = validate(value)
    if (e) { setErr(e); return }
    onConfirm(value)
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" role="dialog" aria-modal="true">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6" onClick={(e)=>e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        {message && <p className="text-sm text-gray-600 mb-4">{message}</p>}
        <div>
          <input
            type="number"
            step={step}
            min={min}
            max={max}
            value={isNaN(value as any) ? '' : value}
            onChange={(e)=> setValue(parseFloat(e.target.value))}
            className={`w-full px-3 py-2 border rounded-lg ${err ? 'border-red-500' : 'border-gray-300'}`}
          />
          {err && <p className="text-xs text-red-600 mt-1">{err}</p>}
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onCancel} className="px-4 py-2 border rounded-lg hover:bg-gray-50">{_cancel}</button>
          <button onClick={onOk} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">{_confirm}</button>
        </div>
      </div>
    </div>
  )
}
