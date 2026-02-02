import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom'
import App from './App'
import UploadPage from './pages/Upload'
import EvaluateUrlPage from './pages/EvaluateUrl'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App>
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/evaluate-url" element={<EvaluateUrlPage />} />
        </Routes>
      </App>
    </BrowserRouter>
  </React.StrictMode>
)

