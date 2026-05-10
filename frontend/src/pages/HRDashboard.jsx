import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getAllSessions } from '../api/client'
import { ChevronRight, Lock, LogOut } from 'lucide-react'

export default function HRDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    sessionStorage.getItem('hr_auth') === 'true'
  )
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isAuthenticated) {
      loadSessions()
    }
  }, [isAuthenticated])

  const loadSessions = async () => {
    try {
      const data = await getAllSessions()
      setSessions(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = (e) => {
    e.preventDefault()
    if (username === 'hris3463' && password === '#7897hrnu') {
      setIsAuthenticated(true)
      sessionStorage.setItem('hr_auth', 'true')
      setLoginError('')
    } else {
      setLoginError('Invalid ID or Password')
    }
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    sessionStorage.removeItem('hr_auth')
    setSessions([])
  }

  const getRecommendationStyle = (rec) => {
    if (!rec) return { color: '#a0a3b5', text: 'Incomplete' }
    const lower = rec.toLowerCase()
    if (lower.includes('strong hire')) return { color: '#34d399', text: 'Strong Hire' }
    if (lower.includes('hire') && !lower.includes('no')) return { color: '#60a5fa', text: 'Hire' }
    if (lower.includes('lean hire')) return { color: '#fbbf24', text: 'Lean Hire' }
    if (lower.includes('no hire') || lower.includes('no')) return { color: '#fb7185', text: 'No Hire' }
    return { color: '#818cf8', text: rec }
  }

  if (!isAuthenticated) {
    return (
      <div className="hr-dashboard page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
        <div className="glass-card" style={{ padding: '40px', maxWidth: '400px', width: '100%', textAlign: 'center' }}>
          <div style={{ background: 'rgba(99, 102, 241, 0.1)', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
            <Lock size={32} color="#818cf8" />
          </div>
          <h2 style={{ marginBottom: '8px' }}>HR Access Restricted</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>Please login to view candidate evaluations.</p>
          
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <input 
              type="text" 
              placeholder="HR ID" 
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              style={{ padding: '12px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'white', borderRadius: '8px', fontSize: '15px' }}
            />
            <input 
              type="password" 
              placeholder="Password" 
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={{ padding: '12px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'white', borderRadius: '8px', fontSize: '15px' }}
            />
            {loginError && <div style={{ color: '#fb7185', fontSize: '14px', textAlign: 'left', marginTop: '-8px' }}>{loginError}</div>}
            <button type="submit" className="btn btn-primary" style={{ marginTop: '8px', width: '100%' }}>
              Secure Login
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="hr-dashboard page">
      <div className="container">
        <div className="report-header animate-fade-in-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
           <div className="report-header-info">
             <h1>HR Dashboard</h1>
             <p style={{ color: 'var(--text-secondary)' }}>Overview of all candidate interview sessions.</p>
           </div>
           <button onClick={handleLogout} className="btn btn-secondary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
             <LogOut size={16} /> Logout
           </button>
        </div>

        <div className="glass-card animate-fade-in-up" style={{ animationDelay: '0.1s', marginTop: '32px', overflowX: 'auto' }}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <div className="spinner" style={{ margin: '0 auto 16px' }} />
              <p>Loading candidates...</p>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '800px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
                  <th style={{ padding: '16px', color: 'var(--text-muted)', fontWeight: 600 }}>Date</th>
                  <th style={{ padding: '16px', color: 'var(--text-muted)', fontWeight: 600 }}>Role</th>
                  <th style={{ padding: '16px', color: 'var(--text-muted)', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '16px', color: 'var(--text-muted)', fontWeight: 600 }}>Overall Score</th>
                  <th style={{ padding: '16px', color: 'var(--text-muted)', fontWeight: 600 }}>Recommendation</th>
                  <th style={{ padding: '16px', color: 'var(--text-muted)', fontWeight: 600 }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => {
                  const recStyle = getRecommendationStyle(s.recommendation)
                  return (
                    <tr key={s.id} style={{ borderBottom: '1px solid var(--border-subtle)' }} className="hr-row-hover">
                      <td style={{ padding: '16px' }}>{new Date(s.created_at).toLocaleDateString()}</td>
                      <td style={{ padding: '16px' }}>
                        <span className="tag" style={{ background: 'var(--bg-tertiary)' }}>{s.role}</span>
                      </td>
                      <td style={{ padding: '16px' }}>
                        <span style={{ opacity: s.status === 'completed' ? 1 : 0.6 }}>
                          {s.status === 'completed' ? '✅ Completed' : '🔄 In Progress'}
                        </span>
                      </td>
                      <td style={{ padding: '16px', fontWeight: 'bold' }}>
                        {s.overall_score ? `${s.overall_score.toFixed(1)}/10` : '-'}
                      </td>
                      <td style={{ padding: '16px', color: recStyle.color, fontWeight: 'bold' }}>
                        {recStyle.text}
                      </td>
                      <td style={{ padding: '16px' }}>
                        {s.status === 'completed' ? (
                          <Link to={`/report/${s.id}`} className="btn btn-secondary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            View Report <ChevronRight size={14} />
                          </Link>
                        ) : (
                           <Link to={`/interview/${s.id}`} className="btn btn-secondary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            Resume <ChevronRight size={14} />
                          </Link>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {sessions.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      No interview sessions found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
