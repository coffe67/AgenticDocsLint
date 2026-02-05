import React, { useState } from 'react'
import ReportView from '../shared/ReportView'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function SprintReportPage() {
  const [jiraText, setJiraText] = useState('')
  const [templatePath, setTemplatePath] = useState('config/sprint_template.yaml')
  const [formats, setFormats] = useState<string[]>(['pptx','json'])
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function toggleFormat(fmt: string) {
    setFormats(prev => prev.includes(fmt) ? prev.filter(x => x !== fmt) : [...prev, fmt])
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const payload = {
        jira: JSON.parse(jiraText),
        formats,
        template_config_path: templatePath || undefined,
      }
      const res = await fetch(`${API_BASE}/generate-sprint-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Sprint Report (Jira → Slides)</h2>
      <form onSubmit={onSubmit} className="card">
        <div>
          <label>Jira JSON</label>
          <textarea rows={10} value={jiraText} onChange={e => setJiraText(e.target.value)} placeholder='{"sprint": {"name": "Sprint 42"}, "issues": []}' />
        </div>
        <div>
          <label>Template config path (optional)</label>
          <input value={templatePath} onChange={e => setTemplatePath(e.target.value)} />
        </div>
        <div className="row">
          <label>Formats</label>
          {['pptx','md','json','png'].map(f => (
            <label key={f} style={{marginRight: 12}}>
              <input type="checkbox" checked={formats.includes(f)} onChange={() => toggleFormat(f)} /> {f}
            </label>
          ))}
        </div>
        <button disabled={!jiraText || loading} type="submit">{loading ? 'Generating...' : 'Generate'}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="card">
          <h3>Artifacts</h3>
          <ul>
            {Object.entries(result.artifacts || {}).map(([k,v]) => (
              <li key={k}><b>{k}:</b> {String(v)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

