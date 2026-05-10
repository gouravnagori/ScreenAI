import { Link, useLocation } from 'react-router-dom'
import './Header.css'

export default function Header() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <header className="header">
      <div className="header-inner container">
        <Link to="/" className="header-brand">
          <div className="header-logo">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="url(#logo-grad)" />
              {/* AI Brain icon */}
              <circle cx="16" cy="12" r="3" stroke="white" strokeWidth="1.5" fill="none"/>
              <circle cx="10" cy="18" r="2" stroke="white" strokeWidth="1.5" fill="none"/>
              <circle cx="22" cy="18" r="2" stroke="white" strokeWidth="1.5" fill="none"/>
              <circle cx="16" cy="24" r="2" stroke="white" strokeWidth="1.5" fill="none"/>
              <line x1="16" y1="15" x2="11" y2="16.5" stroke="white" strokeWidth="1.2"/>
              <line x1="16" y1="15" x2="21" y2="16.5" stroke="white" strokeWidth="1.2"/>
              <line x1="10.5" y1="20" x2="14.5" y2="22.5" stroke="white" strokeWidth="1.2"/>
              <line x1="21.5" y1="20" x2="17.5" y2="22.5" stroke="white" strokeWidth="1.2"/>
              <circle cx="16" cy="12" r="1" fill="white"/>
              <circle cx="10" cy="18" r="0.8" fill="white"/>
              <circle cx="22" cy="18" r="0.8" fill="white"/>
              <circle cx="16" cy="24" r="0.8" fill="white"/>
              <defs>
                <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32">
                  <stop stopColor="#818cf8"/>
                  <stop offset="0.5" stopColor="#a78bfa"/>
                  <stop offset="1" stopColor="#6366f1"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span className="header-title">ScreenAI</span>
          <span className="header-badge">v1.0</span>
        </Link>

        {isHome ? (
          <Link to="/hr" className="btn btn-secondary btn-sm" style={{ border: 'none', background: 'transparent' }}>
             HR Dashboard
          </Link>
        ) : (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <Link to="/hr" className="btn btn-secondary btn-sm" style={{ border: 'none', background: 'transparent' }}>
              HR Dashboard
            </Link>
            <Link to="/" className="btn btn-secondary btn-sm">
              ← New Session
            </Link>
          </div>
        )}
      </div>
    </header>
  )
}
