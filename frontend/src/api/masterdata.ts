import api from '@/api/api'

// Generic types
export type Id = string

// Clients
export type Client = {
  id?: Id
  code?: string
  name: string
  first_name?: string
  last_name?: string
  gender?: 'male'|'female'|'other'
  birthdate?: string
  age?: number
  email?: string
  phone?: string
  address?: string
  postal_code?: string
  country_code?: string
  type?: 'clinic'|'dentist'|'other'
  tax_id?: string
  billing_address?: Record<string, any>
  shipping_address?: Record<string, any>
  default_shipping_address?: string
  payment_terms?: string
  notes?: string
  active?: boolean
  contacts?: Array<Record<string, any>>
  created_at?: string
  location_code?: string
  // Financial preferences (ids)
  preferred_currency?: Id
  payment_type?: Id
  payment_form?: Id
  payment_method?: Id
}

// Laboratories
export type Laboratory = {
  id?: Id
  name: string
  address?: string
  country?: string
  postal_code?: string
  city?: string
  tax_id?: string
  phone?: string
  email?: string
  logo_url?: string
  active?: boolean
}
export async function listLaboratories() {
  const { data } = await api.get(`/masterdata/laboratories`)
  return data as { laboratories: Laboratory[] }
}
export async function createLaboratory(body: Partial<Laboratory>) {
  const { data } = await api.post(`/masterdata/laboratories`, body)
  return data.laboratory as Laboratory
}
export async function updateLaboratory(id: Id, body: Partial<Laboratory>) {
  const { data } = await api.put(`/masterdata/laboratories/${id}`, body)
  return data.laboratory as Laboratory
}

export async function listClients(q = '', page = 1, page_size = 20) {
  const { data } = await api.get(`/masterdata/clients`, { params: { q, page, page_size } })
  return data as { total: number, items: Client[] }
}
export async function createClient(body: Partial<Client>) {
  const { data } = await api.post(`/masterdata/clients`, body)
  return data.client as Client
}
export async function updateClient(id: Id, body: Partial<Client>) {
  const { data } = await api.put(`/masterdata/clients/${id}`, body)
  return data.client as Client
}
export async function deleteClient(id: Id) {
  const { data } = await api.delete(`/masterdata/clients/${id}`)
  return data
}
export async function getClient(id: Id) {
  const { data } = await api.get(`/masterdata/clients/${id}`)
  return data.client as Client
}
export async function searchClientsBrief(q = '') {
  const { data } = await api.get(`/masterdata/clients/search`, { params: { q } })
  return data as { items: Array<{ id: Id; code?: string; name: string; tax_id?: string; email?: string; phone?: string }> }
}

// Countries
export type Country = { id?: Id; code: string; name: string }
export async function listCountries() {
  const { data } = await api.get(`/masterdata/countries`)
  return data as { items: Country[] }
}
export async function createCountry(body: Partial<Country>) {
  const { data } = await api.post(`/masterdata/countries`, body)
  return data.country as Country
}
export async function updateCountry(id: Id, body: Partial<Country>) {
  const { data } = await api.put(`/masterdata/countries/${id}`, body)
  return data.country as Country
}
export async function deleteCountry(id: Id) {
  const { data } = await api.delete(`/masterdata/countries/${id}`)
  return data
}

// Shipping Addresses
export type ShippingAddress = { id?: Id; client?: Id | null; code: string; address1?: string; address2?: string; postal_code?: string; city?: string; country_code?: string }
export async function listShippingAddresses() {
  const { data } = await api.get(`/masterdata/shipping-addresses`)
  return data as { items: ShippingAddress[] }
}
export async function createShippingAddress(body: Partial<ShippingAddress>) {
  const { data } = await api.post(`/masterdata/shipping-addresses`, body)
  return data.shipping_address as ShippingAddress
}
export async function updateShippingAddress(id: Id, body: Partial<ShippingAddress>) {
  const { data } = await api.put(`/masterdata/shipping-addresses/${id}`, body)
  return data.shipping_address as ShippingAddress
}
export async function deleteShippingAddress(id: Id) {
  const { data } = await api.delete(`/masterdata/shipping-addresses/${id}`)
  return data
}

// Client-scoped Shipping Addresses
export async function listClientShippingAddresses(clientId: Id) {
  const { data } = await api.get(`/masterdata/clients/${clientId}/shipping-addresses`)
  return data as { items: ShippingAddress[] }
}
export async function createClientShippingAddress(clientId: Id, body: Partial<ShippingAddress>) {
  const { data } = await api.post(`/masterdata/clients/${clientId}/shipping-addresses`, body)
  return data.shipping_address as ShippingAddress
}
export async function updateClientShippingAddress(clientId: Id, id: Id, body: Partial<ShippingAddress>) {
  const { data } = await api.put(`/masterdata/clients/${clientId}/shipping-addresses/${id}`, body)
  return data.shipping_address as ShippingAddress
}
export async function deleteClientShippingAddress(clientId: Id, id: Id) {
  const { data } = await api.delete(`/masterdata/clients/${clientId}/shipping-addresses/${id}`)
  return data
}

// Client Prices
export type ClientPrice = {
  id?: Id
  client_id?: Id
  sale_type?: string
  sale_code?: string
  code?: string
  uom?: string
  min_qty?: number
  unit_price?: number
  start_date?: string
  end_date?: string
}
export async function listClientPrices(clientId: Id) {
  const { data } = await api.get(`/masterdata/clients/${clientId}/prices`)
  return data as { items: ClientPrice[] }
}
export async function createClientPrice(clientId: Id, body: Partial<ClientPrice>) {
  const { data } = await api.post(`/masterdata/clients/${clientId}/prices`, body)
  return data.price as ClientPrice
}
export async function updateClientPrice(clientId: Id, id: Id, body: Partial<ClientPrice>) {
  const { data } = await api.put(`/masterdata/clients/${clientId}/prices/${id}`, body)
  return data.price as ClientPrice
}
export async function deleteClientPrice(clientId: Id, id: Id) {
  const { data } = await api.delete(`/masterdata/clients/${clientId}/prices/${id}`)
  return data
}

// Client price resolver
export async function resolveClientUnitPrice(clientId: Id, params: { sale_type?: string; code: string; qty?: number; date?: string }) {
  const { data } = await api.get(`/masterdata/clients/${clientId}/resolve-price`, { params })
  return data as { unit_price: number | null }
}

// Patients
export type Patient = {
  id?: Id
  name: string
  first_name?: string
  last_name?: string
  gender?: 'male'|'female'|'other'
  birthdate?: string
  age?: number
  email?: string
  phone?: string
  address?: string
  notes?: string
  created_at?: string
}
export async function listPatients(q = '', page = 1, page_size = 20) {
  const { data } = await api.get(`/masterdata/patients`, { params: { q, page, page_size } })
  return data as { total: number, items: Patient[] }
}
export async function createPatient(body: Partial<Patient>) {
  const { data } = await api.post(`/masterdata/patients`, body)
  return data.patient as Patient
}
export async function updatePatient(id: Id, body: Partial<Patient>) {
  const { data } = await api.put(`/masterdata/patients/${id}`, body)
  return data.patient as Patient
}
export async function deletePatient(id: Id) {
  const { data } = await api.delete(`/masterdata/patients/${id}`)
  return data
}

// Technicians
export type Technician = {
  id?: Id
  name: string
  email?: string
  phone?: string
  workcenter?: string
}
export async function listTechnicians(q = '', page = 1, page_size = 20) {
  const { data } = await api.get(`/masterdata/technicians`, { params: { q, page, page_size } })
  return data as { total: number, items: Technician[] }
}
export async function createTechnician(body: Partial<Technician>) {
  const { data } = await api.post(`/masterdata/technicians`, body)
  return data.technician as Technician
}
export async function updateTechnician(id: Id, body: Partial<Technician>) {
  const { data } = await api.put(`/masterdata/technicians/${id}`, body)
  return data.technician as Technician
}
export async function deleteTechnician(id: Id) {
  const { data } = await api.delete(`/masterdata/technicians/${id}`)
  return data
}

// Services
export type Service = {
  id?: Id
  name: string
  code?: string
  price?: number
  description?: string
}
export async function listServices(q = '', page = 1, page_size = 20) {
  const { data } = await api.get(`/masterdata/services`, { params: { q, page, page_size } })
  return data as { total: number, items: Service[] }
}
export async function createService(body: Partial<Service>) {
  const { data } = await api.post(`/masterdata/services`, body)
  return data.service as Service
}
export async function updateService(id: Id, body: Partial<Service>) {
  const { data } = await api.put(`/masterdata/services/${id}`, body)
  return data.service as Service
}
export async function deleteService(id: Id) {
  const { data } = await api.delete(`/masterdata/services/${id}`)
  return data
}

// Document Types
export type DocumentType = {
  id?: Id
  name: string
  extension?: string
}
export async function listDocumentTypes(q = '', page = 1, page_size = 20) {
  const { data } = await api.get(`/masterdata/document-types`, { params: { q, page, page_size } })
  return data as { total: number, items: DocumentType[] }
}
export async function createDocumentType(body: Partial<DocumentType>) {
  const { data } = await api.post(`/masterdata/document-types`, body)
  return data.document_type as DocumentType
}
export async function updateDocumentType(id: Id, body: Partial<DocumentType>) {
  const { data } = await api.put(`/masterdata/document-types/${id}`, body)
  return data.document_type as DocumentType
}
export async function deleteDocumentType(id: Id) {
  const { data } = await api.delete(`/masterdata/document-types/${id}`)
  return data
}

// Financial
export type Currency = {
  id?: Id
  code: string
  name?: string
  symbol?: string
  is_default?: boolean
  active?: boolean
}
export async function listCurrencies() {
  const { data } = await api.get(`/masterdata/financial/currencies`)
  return data as { items: Currency[] }
}
export async function createCurrency(body: Partial<Currency>) {
  const { data } = await api.post(`/masterdata/financial/currencies`, body)
  return data.currency as Currency
}

export type SimpleNamed = { id?: Id; code?: string; name: string; active?: boolean }
export async function listPaymentTypes() {
  const { data } = await api.get(`/masterdata/financial/payment-types`)
  return data as { items: SimpleNamed[] }
}
export async function createPaymentType(body: Partial<SimpleNamed>) {
  const { data } = await api.post(`/masterdata/financial/payment-types`, body)
  return data.payment_type as SimpleNamed
}

export async function listPaymentForms() {
  const { data } = await api.get(`/masterdata/financial/payment-forms`)
  return data as { items: SimpleNamed[] }
}
export async function createPaymentForm(body: Partial<SimpleNamed>) {
  const { data } = await api.post(`/masterdata/financial/payment-forms`, body)
  return data.payment_form as SimpleNamed
}

export async function listPaymentMethods() {
  const { data } = await api.get(`/masterdata/financial/payment-methods`)
  return data as { items: SimpleNamed[] }
}
export async function createPaymentMethod(body: Partial<SimpleNamed>) {
  const { data } = await api.post(`/masterdata/financial/payment-methods`, body)
  return data.payment_method as SimpleNamed
}

// Series
export type Series = { id?: Id; doc_type: 'order'|'invoice'|'client'; prefix?: string; next_number?: number; padding?: number; active?: boolean }
export async function listSeries() {
  const { data } = await api.get(`/masterdata/financial/series`)
  return data as { items: Series[] }
}
export async function createSeries(body: Partial<Series>) {
  const { data } = await api.post(`/masterdata/financial/series`, body)
  return data.series as Series
}
export async function updateSeries(id: Id, body: Partial<Series>) {
  const { data } = await api.put(`/masterdata/financial/series/${id}`, body)
  return data.series as Series
}

// SMTP Config
export type SmtpConfig = {
  server: string
  port: number
  use_tls?: boolean
  use_ssl?: boolean
  username?: string
  password?: string
  has_password?: boolean
}
export async function getSmtpConfig() {
  const { data } = await api.get(`/masterdata/financial/smtp`)
  return data.smtp as SmtpConfig | null
}
export async function updateSmtpConfig(body: Partial<SmtpConfig>) {
  const { data } = await api.put(`/masterdata/financial/smtp`, body)
  return data.smtp as SmtpConfig
}
export async function testSmtp(to: string) {
  // SMTP test may take longer (multiple fallback attempts server-side)
  const { data } = await api.post(`/masterdata/financial/smtp/test`, { to }, { timeout: 90000 })
  return data as { ok?: boolean; error?: string }
}

export async function diagnoseSmtp() {
  // Diagnostics may collect multiple probes; give it extra time
  const { data } = await api.post(`/masterdata/financial/smtp/diagnose`, {}, { timeout: 90000 })
  return data as any
}
