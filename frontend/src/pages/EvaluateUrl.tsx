import React, { useState } from 'react'
import { evaluateUrl } from '../api/client'
import ReportView from '../shared/ReportView'

export default function EvaluateUrlPage() {
  const [url, setUrl] = useState('')
  const [autoFix, setAutoFix] = useState(true)
  const [configPath, setConfigPath] = useState('config/default.yaml')
  const [allowedExts, setAllowedExts] = useState('pptx,md,txt,json')
  const [crawl, setCrawl] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await evaluateUrl({
        url,
        auto_fix: autoFix,
        config_path: configPath,
        allowed_exts: allowedExts.split(',').map(s => s.trim()).filter(Boolean),
        crawl_links: crawl,
      })
      setResult(data)
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Evaluate From URL</h2>
      <form onSubmit={onSubmit} className="card">
        <div>
          <label>URL</label>
          <input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://example.com/slides.pptx or page.html" />
        </div>
        <div>
          <label>Config path</label>
          <input value={configPath} onChange={e => setConfigPath(e.target.value)} placeholder="config/default.yaml" />
        </div>
        <div>
          <label>Allowed extensions</label>
          <input value={allowedExts} onChange={e => setAllowedExts(e.target.value)} />
        </div>
        <div>
          <label>
            <input type="checkbox" checked={crawl} onChange={e => setCrawl(e.target.checked)} /> Crawl page links
          </label>
        </div>
        <div>
          <label>
            <input type="checkbox" checked={autoFix} onChange={e => setAutoFix(e.target.checked)} /> Auto-fix (generate updates)
          </label>
        </div>
        <button disabled={!url || loading} type="submit">{loading ? 'Evaluating...' : 'Evaluate'}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && <ReportView data={result} />}
    </div>
  )
}

