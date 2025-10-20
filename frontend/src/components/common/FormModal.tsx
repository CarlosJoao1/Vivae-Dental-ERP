import { ReactNode } from 'react'

interface FormModalHeaderProps {
  title: string
  onClose: () => void
  isEdit?: boolean
}

export function FormModalHeader({ title, onClose, isEdit }: FormModalHeaderProps) {
  return (
    <div className="flex justify-between items-center mb-4">
      <h3 className="text-lg font-semibold">
        {isEdit ? `Edit ${title}` : `New ${title}`}
      </h3>
      <button
        type="button"
        onClick={onClose}
        className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
        aria-label="Close dialog"
      >
        ×
      </button>
    </div>
  )
}

interface FormModalFooterProps {
  onCancel: () => void
  loading: boolean
  cancelLabel?: string
  submitLabel?: string
  isEdit?: boolean
}

export function FormModalFooter({
  onCancel,
  loading,
  cancelLabel = 'Cancel',
  submitLabel,
  isEdit
}: FormModalFooterProps) {
  const defaultSubmitLabel = isEdit ? 'Update' : 'Create'
  
  return (
    <div className="flex justify-end space-x-2 pt-4 border-t">
      <button
        type="button"
        onClick={onCancel}
        disabled={loading}
        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
      >
        {cancelLabel}
      </button>
      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
      >
        {loading ? 'Saving...' : (submitLabel || defaultSubmitLabel)}
      </button>
    </div>
  )
}

interface FormModalProps {
  isOpen: boolean
  title: string
  onClose: () => void
  onSubmit: (e: React.FormEvent) => void
  children: ReactNode
  loading: boolean
  isEdit?: boolean
  cancelLabel?: string
  submitLabel?: string
}

export default function FormModal({
  isOpen,
  title,
  onClose,
  onSubmit,
  children,
  loading,
  isEdit,
  cancelLabel,
  submitLabel
}: FormModalProps) {
  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="form-modal-title"
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <FormModalHeader title={title} onClose={onClose} isEdit={isEdit} />
          
          <form onSubmit={onSubmit}>
            {children}
            
            <FormModalFooter
              onCancel={onClose}
              loading={loading}
              cancelLabel={cancelLabel}
              submitLabel={submitLabel}
              isEdit={isEdit}
            />
          </form>
        </div>
      </div>
    </div>
  )
}
