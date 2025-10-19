import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

// Tab types
type MasterDataTab = 'items' | 'uoms' | 'locations' | 'suppliers'

// Type definitions
interface Item {
  id: string
  item_no: string
  description: string
  description_2?: string
  item_type: 'manufactured' | 'purchased' | 'both'
  base_uom: string
  lead_time_days: number
  unit_cost?: number
  status: string
}

interface UOM {
  id: string
  code: string
  description: string
  decimals: number
}

interface Location {
  id: string
  code: string
  name: string
  city?: string
  is_default: boolean
  blocked: boolean
}

interface Supplier {
  id: string
  supplier_id: string
  name: string
  email?: string
  phone_no?: string
  lead_time_days_default: number
  status: string
}

export default function ProductionMasterData() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<MasterDataTab>('items')
  
  // Data states
  const [items, setItems] = useState<Item[]>([])
  const [uoms, setUOMs] = useState<UOM[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  
  // UI states
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingItem, setEditingItem] = useState<any>(null)
  const [searchQuery, setSearchQuery] = useState('')
  
  useEffect(() => {
    loadData()
  }, [activeTab])
  
  const loadData = async () => {
    setLoading(true)
    try {
      switch (activeTab) {
        case 'items':
          const itemsRes = await api<any>('/api/production/masterdata/items')
          setItems(itemsRes.items || [])
          break
        case 'uoms':
          const uomsRes = await api<any>('/api/production/masterdata/uom')
          setUOMs(uomsRes.items || [])
          break
        case 'locations':
          const locsRes = await api<any>('/api/production/masterdata/locations')
          setLocations(locsRes.items || [])
          break
        case 'suppliers':
          const suppRes = await api<any>('/api/production/masterdata/suppliers')
          setSuppliers(suppRes.items || [])
          break
      }
    } catch (err: any) {
      toast.error(`Failed to load data: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }
  
  const handleCreate = () => {
    setEditingItem(null)
    setShowForm(true)
  }
  
  const handleEdit = (item: any) => {
    setEditingItem(item)
    setShowForm(true)
  }
  
  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete ${name}?`)) return
    
    try {
      const endpoint = {
        items: `/api/production/masterdata/items/${id}`,
        uoms: `/api/production/masterdata/uom/${id}`,
        locations: `/api/production/masterdata/locations/${id}`,
        suppliers: `/api/production/masterdata/suppliers/${id}`,
      }[activeTab]
      
      await api(endpoint, { method: 'DELETE' })
      toast.success(`✅ ${name} deleted successfully!`)
      loadData()
    } catch (err: any) {
      toast.error(`❌ Failed to delete: ${err.message}`)
    }
  }
  
  const handleFormClose = () => {
    setShowForm(false)
    setEditingItem(null)
    loadData()
  }
  
  // Filter data by search
  const getFilteredData = () => {
    const query = searchQuery.toLowerCase()
    switch (activeTab) {
      case 'items':
        return items.filter(i => 
          i.item_no.toLowerCase().includes(query) || 
          i.description.toLowerCase().includes(query)
        )
      case 'uoms':
        return uoms.filter(u => 
          u.code.toLowerCase().includes(query) || 
          u.description.toLowerCase().includes(query)
        )
      case 'locations':
        return locations.filter(l => 
          l.code.toLowerCase().includes(query) || 
          l.name.toLowerCase().includes(query)
        )
      case 'suppliers':
        return suppliers.filter(s => 
          s.supplier_id.toLowerCase().includes(query) || 
          s.name.toLowerCase().includes(query)
        )
    }
  }
  
  const tabs = [
    { key: 'items', label: '📦 Items', icon: '📦' },
    { key: 'uoms', label: '📏 UOMs', icon: '📏' },
    { key: 'locations', label: '📍 Locations', icon: '📍' },
    { key: 'suppliers', label: '🏭 Suppliers', icon: '🏭' },
  ]
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            🗃️ {t('master_data') || 'Master Data'}
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            {t('master_data_desc') || 'Manage production master data: items, units of measure, locations, and suppliers'}
          </p>
        </div>
        
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          ➕ {t('create_new') || 'Create New'}
        </button>
      </div>
      
      {/* Tabs */}
      <div className="card p-0 overflow-hidden">
        <div className="flex border-b">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as MasterDataTab)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        
        {/* Search Bar */}
        <div className="p-4 border-b bg-gray-50">
          <input
            type="text"
            placeholder={`🔍 Search ${activeTab}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg"
          />
        </div>
        
        {/* Content */}
        <div className="p-4">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin text-4xl mb-4">⏳</div>
              <p className="text-gray-600">{t('loading') || 'Loading...'}</p>
            </div>
          ) : (
            <>
              {activeTab === 'items' && <ItemsTable items={getFilteredData() as Item[]} onEdit={handleEdit} onDelete={handleDelete} />}
              {activeTab === 'uoms' && <UOMsTable uoms={getFilteredData() as UOM[]} onEdit={handleEdit} onDelete={handleDelete} />}
              {activeTab === 'locations' && <LocationsTable locations={getFilteredData() as Location[]} onEdit={handleEdit} onDelete={handleDelete} />}
              {activeTab === 'suppliers' && <SuppliersTable suppliers={getFilteredData() as Supplier[]} onEdit={handleEdit} onDelete={handleDelete} />}
            </>
          )}
        </div>
      </div>
      
      {/* Form Modal (placeholder) */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h2 className="text-xl font-semibold">
                {editingItem ? '✏️ Edit' : '➕ Create'} {activeTab.slice(0, -1)}
              </h2>
              <button onClick={handleFormClose} className="text-2xl hover:text-red-600">
                ×
              </button>
            </div>
            <div className="p-6">
              <p className="text-gray-600">
                Form component coming soon! API is ready at:
                <br />
                <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                  /api/production/masterdata/{activeTab}
                </code>
              </p>
              <button
                onClick={handleFormClose}
                className="mt-4 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================
// TABLE COMPONENTS
// ============================================

function ItemsTable({ items, onEdit, onDelete }: { items: Item[], onEdit: (item: Item) => void, onDelete: (id: string, name: string) => void }) {
  if (items.length === 0) {
    return <EmptyState message="No items found. Create your first product!" />
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item No</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">UOM</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lead Time</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map(item => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-mono text-sm">{item.item_no}</td>
              <td className="px-4 py-3 text-sm">
                <div className="font-medium">{item.description}</div>
                {item.description_2 && <div className="text-xs text-gray-500">{item.description_2}</div>}
              </td>
              <td className="px-4 py-3 text-sm">
                <span className={`px-2 py-1 rounded text-xs ${
                  item.item_type === 'manufactured' ? 'bg-blue-100 text-blue-800' :
                  item.item_type === 'purchased' ? 'bg-green-100 text-green-800' :
                  'bg-purple-100 text-purple-800'
                }`}>
                  {item.item_type}
                </span>
              </td>
              <td className="px-4 py-3 text-sm">{item.base_uom}</td>
              <td className="px-4 py-3 text-sm">{item.lead_time_days} days</td>
              <td className="px-4 py-3 text-sm">
                <span className={`px-2 py-1 rounded text-xs ${
                  item.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {item.status}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <button onClick={() => onEdit(item)} className="text-blue-600 hover:text-blue-800 mr-3">
                  ✏️
                </button>
                <button onClick={() => onDelete(item.id, item.item_no)} className="text-red-600 hover:text-red-800">
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function UOMsTable({ uoms, onEdit, onDelete }: { uoms: UOM[], onEdit: (uom: UOM) => void, onDelete: (id: string, name: string) => void }) {
  if (uoms.length === 0) {
    return <EmptyState message="No UOMs found. Create your first unit of measure!" />
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Decimals</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {uoms.map(uom => (
            <tr key={uom.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-mono text-sm font-medium">{uom.code}</td>
              <td className="px-4 py-3 text-sm">{uom.description}</td>
              <td className="px-4 py-3 text-sm">{uom.decimals}</td>
              <td className="px-4 py-3 text-right">
                <button onClick={() => onEdit(uom)} className="text-blue-600 hover:text-blue-800 mr-3">
                  ✏️
                </button>
                <button onClick={() => onDelete(uom.id, uom.code)} className="text-red-600 hover:text-red-800">
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function LocationsTable({ locations, onEdit, onDelete }: { locations: Location[], onEdit: (loc: Location) => void, onDelete: (id: string, name: string) => void }) {
  if (locations.length === 0) {
    return <EmptyState message="No locations found. Create your first warehouse/location!" />
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">City</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Default</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {locations.map(loc => (
            <tr key={loc.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-mono text-sm font-medium">{loc.code}</td>
              <td className="px-4 py-3 text-sm">{loc.name}</td>
              <td className="px-4 py-3 text-sm">{loc.city || '-'}</td>
              <td className="px-4 py-3 text-sm">
                {loc.is_default && <span className="text-green-600">✓ Default</span>}
              </td>
              <td className="px-4 py-3 text-sm">
                <span className={`px-2 py-1 rounded text-xs ${
                  loc.blocked ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                }`}>
                  {loc.blocked ? 'Blocked' : 'Active'}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <button onClick={() => onEdit(loc)} className="text-blue-600 hover:text-blue-800 mr-3">
                  ✏️
                </button>
                <button onClick={() => onDelete(loc.id, loc.code)} className="text-red-600 hover:text-red-800">
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SuppliersTable({ suppliers, onEdit, onDelete }: { suppliers: Supplier[], onEdit: (sup: Supplier) => void, onDelete: (id: string, name: string) => void }) {
  if (suppliers.length === 0) {
    return <EmptyState message="No suppliers found. Create your first vendor!" />
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contact</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lead Time</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {suppliers.map(sup => (
            <tr key={sup.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-mono text-sm font-medium">{sup.supplier_id}</td>
              <td className="px-4 py-3 text-sm">{sup.name}</td>
              <td className="px-4 py-3 text-sm">
                <div className="text-xs">
                  {sup.email && <div>📧 {sup.email}</div>}
                  {sup.phone_no && <div>📞 {sup.phone_no}</div>}
                </div>
              </td>
              <td className="px-4 py-3 text-sm">{sup.lead_time_days_default} days</td>
              <td className="px-4 py-3 text-sm">
                <span className={`px-2 py-1 rounded text-xs ${
                  sup.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {sup.status}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <button onClick={() => onEdit(sup)} className="text-blue-600 hover:text-blue-800 mr-3">
                  ✏️
                </button>
                <button onClick={() => onDelete(sup.id, sup.supplier_id)} className="text-red-600 hover:text-red-800">
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-12">
      <div className="text-6xl mb-4">📭</div>
      <p className="text-gray-600">{message}</p>
    </div>
  )
}
