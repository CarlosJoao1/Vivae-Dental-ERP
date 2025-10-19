// Garante tipos do Vite
/// <reference types="vite/client" />

import axiosApi from '@/api/api'

const RAW = import.meta.env.VITE_API_BASE || "";
// Remove barra no fim ("/") para normalizar
export const API_BASE = RAW.replace(/\/+$/, "");

/**
 * Helper básico para chamadas à API usando axios (com auth automática)
 * Mantém compatibilidade com código antigo que usa fetch-style API
 */
export async function api<T = unknown>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  // Remove /api prefix se presente (axios já adiciona)
  const cleanPath = path.replace(/^\/api/, '')
  
  try {
    const method = (init.method || 'GET').toUpperCase()
    const body = init.body ? JSON.parse(init.body as string) : undefined
    
    let response
    switch (method) {
      case 'GET':
        response = await axiosApi.get(cleanPath)
        break
      case 'POST':
        response = await axiosApi.post(cleanPath, body)
        break
      case 'PATCH':
      case 'PUT':
        response = await axiosApi.patch(cleanPath, body)
        break
      case 'DELETE':
        response = await axiosApi.delete(cleanPath)
        break
      default:
        throw new Error(`Unsupported method: ${method}`)
    }
    
    return response.data as T
  } catch (error: any) {
    // Extract error message from axios response
    const msg = error.response?.data?.error || error.response?.data?.message || error.message || 'Request failed'
    throw new Error(msg)
  }
}
