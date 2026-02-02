const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function uploadEvaluate(file: File, autoFix: boolean, configPath?: string) {
  const form = new FormData()
  form.append('file', file)
  form.append('auto_fix', String(autoFix))
  if (configPath) form.append('config_path', configPath)
  const res = await fetch(`${API_BASE}/evaluate`, {
    method: 'POST',
    body: form
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function evaluateUrl(payload: {
  url: string
  auto_fix?: boolean
  config_path?: string
  allowed_exts?: string[]
  crawl_links?: boolean
}) {
  const res = await fetch(`${API_BASE}/evaluate-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

