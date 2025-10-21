import { useState, useEffect } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

interface BOMLine {
  line_no: number
  component_item_no: string
  description: string
  quantity_per: number
  uom_code: string
  scrap_pct: number
  component_type: string
  position: string
}

interface BOMFormData {
  item_no: string
  version_code: string
  base_uom: string
  status: string
  lines: BOMLine[]
}

interface BOMFormProps {
  bom?: any
  onSuccess: () => void
  onCancel: () => void
}

export default function BOMForm({ bom, onSuccess, onCancel }: BOMFormProps) {
  const { t } = useTranslation()
  const [items, setItems] = useState<any[]>([])
  const [uoms, setUOMs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const isEditMode = !!bom
  
  const { register, control, handleSubmit, watch, formState: { errors } } = useForm<BOMFormData>({
    defaultValues: bom ? {
      item_no: bom.item_no,
      version_code: bom.version_code,
      base_uom: bom.base_uom,
      status: bom.status,
      lines: bom.lines || []
    } : {
      item_no: '',
      version_code: 'V1',
      base_uom: 'UN',
      status: 'New',
      lines: [{ line_no: 10, component_item_no: '', description: '', quantity_per: 1, uom_code: 'UN', scrap_pct: 0, component_type: 'Item', position: '' }]
    }
  })
  
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'lines'
  })
  
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    try {
      const [itemsRes, uomsRes] = await Promise.all([
        api<any>('/api/production/masterdata/items'),
        api<any>('/api/production/masterdata/uoms')
      ])
      setItems(Array.isArray(itemsRes) ? itemsRes : (itemsRes?.items || []))
      setUOMs(Array.isArray(uomsRes) ? uomsRes : (uomsRes?.items || []))
    } catch (err: any) {
      console.error('Failed to load form data:', err)
    }
  }
  
  const onSubmit = async (data: BOMFormData) => {
    setLoading(true)
    setError('')
    
    try {
      // Validate at least one line
      if (data.lines.length === 0) {
        setError('At least one BOM line is required')
        setLoading(false)
        return
      }
      
      // Validate quantities
      for (const line of data.lines) {
        if (line.quantity_per <= 0) {
          setError(`Line ${line.line_no}: Quantity must be > 0`)
          setLoading(false)
          return
        }
        if (line.scrap_pct < 0 || line.scrap_pct > 100) {
          setError(`Line ${line.line_no}: Scrap % must be between 0 and 100`)
          setLoading(false)
          return
        }
      }
      
      if (isEditMode) {
        // Update existing BOM
        await api(`/api/production/boms/${bom.id}`, {
          method: 'PATCH',
          body: JSON.stringify(data)
        })
        toast.success(`✅ BOM ${data.item_no} ${data.version_code} updated successfully!`)
      } else {
        // Create new BOM
        await api('/api/production/boms', {
          method: 'POST',
          body: JSON.stringify(data)
        })
        toast.success(`✅ BOM ${data.item_no} ${data.version_code} created successfully!`)
      }
      
      onSuccess()
    } catch (err: any) {
      toast.error(`❌ Failed to save BOM: ${err.message}`)
      setError(err.message || 'Failed to save BOM')
      setLoading(false)
    }
  }
  
  const addLine = () => {
    const lastLineNo = fields.length > 0 ? fields[fields.length - 1].line_no : 0
    append({
      line_no: lastLineNo + 10,
      component_item_no: '',
      description: '',
      quantity_per: 1,
      uom_code: 'UN',
      scrap_pct: 0,
      component_type: 'Item',
      position: ''
    })
  }
  
  const handleItemChange = (index: number, itemNo: string) => {
    const item = items.find(i => i.item_no === itemNo)
    if (item) {
      // Auto-fill description and UOM
      const lineElement = document.querySelector(`[name="lines.${index}.description"]`) as HTMLInputElement
      const uomElement = document.querySelector(`[name="lines.${index}.uom_code"]`) as HTMLSelectElement
      if (lineElement) lineElement.value = item.description || ''
      if (uomElement) uomElement.value = item.base_uom || 'UN'
    }
  }
  
  // Get manufactured items for item_no field
  const manufacturedItems = items.filter(i => i.item_type === 'manufactured' || i.item_type === 'semi-finished')
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">
            {isEditMode ? `📝 ${t('edit_bom') || 'Edit BOM'}` : `➕ ${t('create_bom') || 'Create BOM'}`}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {t('bom_form_desc') || 'Bill of Materials - Define components for manufactured items'}
          </p>
        </div>
        
        {/* Form Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <form id="bom-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Error Banner */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                ❌ {error}
              </div>
            )}
            
            {/* Header Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('item_no') || 'Item No'} <span className="text-red-600">*</span>
                </label>
                <select
                  {...register('item_no', { required: 'Item is required' })}
                  disabled={isEditMode}
                  className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100"
                >
                  <option value="">{t('select') || 'Select...'}</option>
                  {manufacturedItems.map(item => (
                    <option key={item.item_no} value={item.item_no}>
                      {item.item_no} - {item.description}
                    </option>
                  ))}
                </select>
                {errors.item_no && (
                  <p className="text-xs text-red-600 mt-1">{errors.item_no.message}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('version_code') || 'Version'} <span className="text-red-600">*</span>
                </label>
                <input
                  type="text"
                  {...register('version_code', { required: 'Version is required' })}
                  disabled={isEditMode}
                  className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100"
                  placeholder="V1"
                />
                {errors.version_code && (
                  <p className="text-xs text-red-600 mt-1">{errors.version_code.message}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('base_uom') || 'Base UOM'}
                </label>
                <select
                  {...register('base_uom')}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {uoms.map(uom => (
                    <option key={uom.code} value={uom.code}>
                      {uom.code} - {uom.description}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">
                  {t('status') || 'Status'}
                </label>
                <select
                  {...register('status')}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="New">{t('new') || 'New'}</option>
                  <option value="Under Development">{t('under_development') || 'Under Development'}</option>
                  <option value="Certified">{t('certified') || 'Certified'}</option>
                  <option value="Closed">{t('closed') || 'Closed'}</option>
                </select>
              </div>
            </div>
            
            {/* BOM Lines */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">{t('bom_lines') || 'BOM Lines'}</h3>
                <button
                  type="button"
                  onClick={addLine}
                  className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                >
                  ➕ {t('add_line') || 'Add Line'}
                </button>
              </div>
              
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-2 py-2 text-left w-16">{t('line') || 'Line'}</th>
                      <th className="px-2 py-2 text-left">{t('component') || 'Component'}</th>
                      <th className="px-2 py-2 text-left">{t('description') || 'Description'}</th>
                      <th className="px-2 py-2 text-left w-24">{t('qty_per') || 'Qty/Per'}</th>
                      <th className="px-2 py-2 text-left w-20">{t('uom') || 'UOM'}</th>
                      <th className="px-2 py-2 text-left w-20">{t('scrap') || 'Scrap %'}</th>
                      <th className="px-2 py-2 text-left w-24">{t('type') || 'Type'}</th>
                      <th className="px-2 py-2 text-left w-24">{t('position') || 'Position'}</th>
                      <th className="px-2 py-2 w-12"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {fields.map((field, index) => (
                      <tr key={field.id} className="border-t">
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            {...register(`lines.${index}.line_no` as const)}
                            className="w-full px-2 py-1 border rounded text-sm"
                            step="10"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <select
                            {...register(`lines.${index}.component_item_no` as const, { required: true })}
                            onChange={(e) => handleItemChange(index, e.target.value)}
                            className="w-full px-2 py-1 border rounded text-sm"
                          >
                            <option value="">Select...</option>
                            {items.map(item => (
                              <option key={item.item_no} value={item.item_no}>
                                {item.item_no}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="text"
                            {...register(`lines.${index}.description` as const)}
                            className="w-full px-2 py-1 border rounded text-sm"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            {...register(`lines.${index}.quantity_per` as const, { required: true, min: 0.001 })}
                            className="w-full px-2 py-1 border rounded text-sm"
                            step="0.001"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <select
                            {...register(`lines.${index}.uom_code` as const)}
                            className="w-full px-2 py-1 border rounded text-sm"
                          >
                            {uoms.map(uom => (
                              <option key={uom.code} value={uom.code}>
                                {uom.code}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            {...register(`lines.${index}.scrap_pct` as const, { min: 0, max: 100 })}
                            className="w-full px-2 py-1 border rounded text-sm"
                            step="0.1"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <select
                            {...register(`lines.${index}.component_type` as const)}
                            className="w-full px-2 py-1 border rounded text-sm"
                          >
                            <option value="Item">Item</option>
                            <option value="Resource">Resource</option>
                          </select>
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="text"
                            {...register(`lines.${index}.position` as const)}
                            className="w-full px-2 py-1 border rounded text-sm"
                            placeholder="Optional"
                          />
                        </td>
                        <td className="px-2 py-2 text-center">
                          <button
                            type="button"
                            onClick={() => remove(index)}
                            disabled={fields.length === 1}
                            className="text-red-600 hover:text-red-800 disabled:text-gray-400 disabled:cursor-not-allowed"
                            title={t('remove_line') || 'Remove line'}
                          >
                            🗑️
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {fields.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  {t('no_lines') || 'No lines added. Click "Add Line" to start.'}
                </p>
              )}
            </div>
          </form>
        </div>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            {t('cancel') || 'Cancel'}
          </button>
          <button
            type="submit"
            form="bom-form"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '⏳ Saving...' : (isEditMode ? '💾 Update' : '➕ Create')}
          </button>
        </div>
      </div>
    </div>
  )
}
