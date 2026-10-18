/**
 * Thin wrappers around the backend API (see backend/app/api/*.py).
 * Kept as plain functions (not a class) so components can import only
 * what they need, and so swapping the base URL for deployment is a
 * one-line change.
 */
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (body?.detail) detail = body.detail
    } catch {
      // response wasn't JSON -- keep the generic message
    }
    const error = new Error(detail)
    error.status = response.status
    throw error
  }

  return response.json()
}

export function fetchVariant(variantId) {
  return request(`/api/variant/${encodeURIComponent(variantId)}`)
}

export function fetchFunctionalEffect(variantId) {
  return request(`/api/variant/${encodeURIComponent(variantId)}/functional-effect`)
}

export function fetchPathway(pathwayId) {
  return request(`/api/pathway/${encodeURIComponent(pathwayId)}`)
}

export function fetchDemoVariants() {
  return request('/api/demo/variants')
}

export function fetchDemoPathways() {
  return request('/api/demo/pathways')
}

export function runSimulation({ variantId, pathwayId }) {
  return request('/api/simulate', {
    method: 'POST',
    body: JSON.stringify({ variant_id: variantId, pathway_id: pathwayId ?? null }),
  })
}
