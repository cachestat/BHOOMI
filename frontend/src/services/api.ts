import { Location, SuperResolutionResult } from '../types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.json() as { detail?: string }
      detail = body.detail || ''
    } catch {
      detail = ''
    }
    throw new Error(detail || `Request failed (${response.status}).`)
  }
  return response.json() as Promise<T>
}

export async function generateSuperResolution(location: Location, date: string) {
  const health = await request<{ demo_mode: boolean }>('/health')
  const path = health.demo_mode ? '/srm/demo' : '/srm/live'
  return request<SuperResolutionResult>(path, {
    method: 'POST',
    body: JSON.stringify({
      bbox: location.bbox,
      latitude: location.latitude,
      longitude: location.longitude,
      date,
    }),
  })
}