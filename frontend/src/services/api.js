const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '')

async function requestSimplification(path, init) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init)
  } catch {
    throw new Error('Could not reach EasyForm AI. Check the backend service and API URL.')
  }

  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(payload.detail || 'Something went wrong while simplifying this document.')
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