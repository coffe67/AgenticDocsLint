import React, { useState } from 'react'
import { uploadEvaluate } from '../api/client'
import ReportView from '../shared/ReportView'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [autoFix, setAutoFix] = useState(true)
  const [configPath, setConfigPath] = useState('config/default.yaml')
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    setError(null)
    setLoading(true)
    try {
      const data = await uploadEvaluate(file, autoFix, configPath)
      setResult(data)
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Evaluate Uploaded File</h2>
      <form onSubmit={onSubmit} className="card">
        <div>
          <label>File</label>
          <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} />
        </div>
        <div>
          <label>Config path</label>
          <input value={configPath} onChange={e => setConfigPath(e.target.value)} placeholder="config/default.yaml" />
        </div>
        <div>
          <label>
            <input type="checkbox" checked={autoFix} onChange={e => setAutoFix(e.target.checked)} /> Auto-fix (generate updates)
          </label>
        </div>
        <button disabled={!file || loading} type="submit">{loading ? 'Evaluating...' : 'Evaluate'}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && <ReportView data={result} />}
    </div>
  )
}

