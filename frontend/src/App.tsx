import { Link, useLocation } from 'react-router-dom'
import React from 'react'

export default function App({ children }: { children: React.ReactNode }) {
  const loc = useLocation()
  return (
    <div className="container">
      <header>
        <h1>SlideForge</h1>
        <nav>
          <Link className={loc.pathname.startsWith('/upload') ? 'active' : ''} to="/upload">Upload</Link>
          <Link className={loc.pathname.startsWith('/evaluate-url') ? 'active' : ''} to="/evaluate-url">From URL</Link>
          <a href="/HowItWorksStepByStep.md" target="_blank" rel="noreferrer">Docs</a>
        </nav>
      </header>
      <main>
        {children}
      </main>
      <footer>
        <small>v0.1 — Local prototype</small>
      </footer>
    </div>
  )
}

