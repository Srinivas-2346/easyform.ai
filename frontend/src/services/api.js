const DEFAULT_PRODUCTION_API_URL = 'https://easyform-ai-api.onrender.com'
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? DEFAULT_PRODUCTION_API_URL : '')
).trim().replace(/\/+$/, '')

async function requestSimplification(path, init) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init)
  } catch {
    throw new Error('Could not reach the API. Check the backend URL and its CORS_ORIGINS setting.')
  }

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json().catch(() => ({}))
    : {}
  if (!response.ok) {
    if (payload.detail) throw new Error(payload.detail)
    if (payload.error?.message) throw new Error(payload.error.message)
    if (!contentType.includes('application/json')) {
      throw new Error(`The API returned a non-JSON HTTP ${response.status} response. Check VITE_API_BASE_URL and the backend deployment.`)
    }
    throw new Error(payload.message || `The API returned HTTP ${response.status}.`)
  }
  if (!contentType.includes('application/json')) {
    throw new Error('The API returned an unexpected response format. Check VITE_API_BASE_URL and the backend deployment.')
  }
  return payload
}

export function simplifyText(text) {
  return requestSimplification('/api/simplify/text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}

export function simplifyPdf(file) {
  const formData = new FormData()
  formData.append('file', file)
  return requestSimplification('/api/simplify/pdf', { method: 'POST', body: formData })
}