import api from '@/api/api'
import type { Id } from '@/api/masterdata'

export type Line = { description: string; qty: number; price: number; total?: number; discount_rate?: number; discount_amount?: number }
export type Order = { id?: Id; number?: string; date?: string; client?: Id | string; currency?: string; lines?: Line[]; total?: number; series?: Id | string; notes?: string; discount_rate?: number; discount_amount?: number; tax_rate?: number; tax_amount?: number }
export type Invoice = { id?: Id; number?: string; date?: string; client?: Id | string; currency?: string; lines?: Line[]; total?: number; status?: string; series?: Id | string; notes?: string; discount_rate?: number; discount_amount?: number; tax_rate?: number; tax_amount?: number }

export async function listOrders() {
  const { data } = await api.get(`/sales/orders`)
  return data as { items: Order[] }
}
export async function createOrder(body: Partial<Order>) {
  const { data } = await api.post(`/sales/orders`, body)
  return data
}
export async function getOrder(id: Id) {
  const { data } = await api.get(`/sales/orders/${id}`)
  return data.order as Order
}
export async function updateOrder(id: Id, body: Partial<Order>) {
  const { data } = await api.put(`/sales/orders/${id}`, body)
  return data.order as Order
}
export function orderPdfUrl(id: Id) { return `${api.defaults.baseURL}/sales/orders/${id}/pdf` }
export async function sendOrderEmail(id: Id, payload: { to?: string; cc?: string; bcc?: string }) {
  const { data } = await api.post(`/sales/orders/${id}/email`, payload)
  return data
}

export async function listInvoices() {
  const { data } = await api.get(`/sales/invoices`)
  return data as { items: Invoice[] }
}
export async function createInvoice(body: Partial<Invoice>) {
  const { data } = await api.post(`/sales/invoices`, body)
  return data
}
export async function getInvoice(id: Id) {
  const { data } = await api.get(`/sales/invoices/${id}`)
  return data.invoice as Invoice
}
export async function updateInvoice(id: Id, body: Partial<Invoice>) {
  const { data } = await api.put(`/sales/invoices/${id}`, body)
  return data.invoice as Invoice
}
export function invoicePdfUrl(id: Id) { return `${api.defaults.baseURL}/sales/invoices/${id}/pdf` }
export async function sendInvoiceEmail(id: Id, payload: { to?: string; cc?: string; bcc?: string }) {
  const { data } = await api.post(`/sales/invoices/${id}/email`, payload)
  return data
}
