import React from 'react'

export default function ReportView({ data }: { data: any }) {
  // The API returns either { report, artifacts, run_workspace } for upload
  // or { results: [{ url, report|error, artifacts }], run_workspace } for URL
  if (data.results) {
    return (
      <div className="card">
        <h3>Results</h3>
        {data.results.map((r: any, i: number) => (
          <div key={i} className="result-block">
            <div className="row"><b>URL:</b> {r.url}</div>
            {r.error ? (
              <div className="error">{r.error}</div>
            ) : (
              r.report && <ReportCore report={r.report} />
            )}
          </div>
        ))}
      </div>
    )
  }
  return (
    <div className="card">
      <h3>Report</h3>
      <ReportCore report={data.report} />
    </div>
  )
}

function ReportCore({ report }: { report: any }) {
  if (!report) return <div>No report</div>
  const overall = report.overall || {}
  return (
    <div className="report">
      <div className="row"><b>Status:</b> {overall.status}</div>
      <div className="row"><b>Score:</b> {overall.score?.toFixed ? overall.score.toFixed(2) : overall.score}</div>
      <div className="row"><b>Update Required:</b> {String(overall.update_required)}</div>
      {Array.isArray(overall.reasons) && overall.reasons.length > 0 && (
        <div className="block">
          <b>Decision rationale:</b>
          <ul>
            {overall.reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
      <div className="block">
        <b>Per-slide summary:</b>
        <ul>
          {report.per_slide?.map((s: any) => (
            <li key={s.slide_index}>
              Slide {s.slide_index} [{s.section ?? 'unknown'}]
              {s.keyword_result ? ` coverage=${(s.keyword_result.coverage ?? 0).toFixed(2)} missing=[${(s.keyword_result.missing || []).join(', ')}]` : ' (no keywords)'}
            </li>
          ))}
        </ul>
      </div>
      {Array.isArray(report.section_summaries) && report.section_summaries.length > 0 && (
        <div className="block">
          <b>Section summaries:</b>
          <ul>
            {report.section_summaries.map((s: any, i: number) => (
              <li key={i}>
                {s.section}: slides={s.slides} avg_cov={s.avg_coverage} below_min=[{(s.below_min_slides || []).join(', ')}]
              </li>
            ))}
          </ul>
        </div>
      )}
      {Array.isArray(overall.recommendations) && overall.recommendations.length > 0 && (
        <div className="block">
          <b>Recommendations:</b>
          <ul>
            {overall.recommendations.map((r: string, i: number) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}

