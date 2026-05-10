import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { startSession } from '../api/client'
import './LandingPage.css'

const ROLES = [
  {
    id: 'AI/ML Engineer',
    title: 'AI/ML Engineer',
    icon: '🧠',
    desc: 'Deep learning, NLP, model training & deployment',
    color: '#818cf8',
  },
  {
    id: 'Data Scientist',
    title: 'Data Scientist',
    icon: '📊',
    desc: 'Data analysis, statistical modeling & visualization',
    color: '#34d399',
  },
  {
    id: 'Backend Engineer',
    title: 'Backend Engineer',
    icon: '⚙️',
    desc: 'APIs, databases, system design & scalability',
    color: '#60a5fa',
  },
  {
    id: 'Full-Stack Developer',
    title: 'Full-Stack Developer',
    icon: '🚀',
    desc: 'Frontend, backend, end-to-end development',
    color: '#fbbf24',
  },
]

export default function LandingPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [selectedRole, setSelectedRole] = useState(null)
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [loadingText, setLoadingText] = useState('Analyzing Resume & Generating Questions...')

  useEffect(() => {
    if (!loading) {
      setLoadingText('Analyzing Resume & Generating Questions...')
      return
    }
    const texts = [
      'Extracting Skills & Experience...',
      'Matching to Role Knowledge Base...',
      'Synthesizing Interview Strategy...',
      'Calibrating Difficulty...',
      'Finalizing Question Set...'
    ]
    let i = 0
    const interval = setInterval(() => {
      i = (i + 1) % texts.length
      setLoadingText(texts[i])
    }, 2500)
    return () => clearInterval(interval)
  }, [loading])

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const validateAndSetFile = (f) => {
    setError('')
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['pdf', 'txt', 'text'].includes(ext)) {
      setError('Please upload a PDF or text file')
      return
    }
    if (f.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum 10MB')
      return
    }
    setFile(f)
  }

  const handleStart = async () => {
    if (!file || !selectedRole) return
    setLoading(true)
    setError('')
    try {
      const data = await startSession(file, selectedRole)
      navigate(`/interview/${data.session_id}`, { state: data })
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to start session'
      setError(msg)
      setLoading(false)
    }
  }

  const canStart = file && selectedRole && !loading

  return (
    <div className="landing page">
      {/* Animated background */}
      <div className="landing-bg">
        <div className="landing-orb landing-orb-1" />
        <div className="landing-orb landing-orb-2" />
        <div className="landing-orb landing-orb-3" />
      </div>

      <div className="container">
        {/* Hero Section */}
        <section className="hero animate-fade-in-up">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            AI-Powered Technical Screening
          </div>
          <h1 className="hero-title">
            Intelligent Candidate <br />
            <span className="gradient-text">Screening System</span>
          </h1>
          <p className="hero-subtitle">
            Upload your resume, select a role, and experience an AI-driven interview
            powered by RAG technology with domain-specific knowledge bases.
          </p>
        </section>

        {/* Resume Upload */}
        <section className="upload-section animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
          <h3 className="section-title">
            <span className="section-number">1</span>
            Upload Your Resume
          </h3>
          <div
            className={`upload-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.text"
              onChange={handleFileChange}
              hidden
            />
            {file ? (
              <div className="upload-success">
                <div className="upload-file-icon">📄</div>
                <div className="upload-file-info">
                  <span className="upload-file-name">{file.name}</span>
                  <span className="upload-file-size">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <button
                  className="upload-remove"
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="upload-placeholder">
                <div className="upload-icon">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <path d="M24 32V16m0 0l-6 6m6-6l6 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M40 30v4a4 4 0 01-4 4H12a4 4 0 01-4-4v-4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <p className="upload-text">
                  <strong>Drag & drop</strong> your resume here, or <strong>click</strong> to browse
                </p>
                <p className="upload-hint">PDF or Text • Max 10MB</p>
              </div>
            )}
          </div>
        </section>

        {/* Role Selection */}
        <section className="role-section animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
          <h3 className="section-title">
            <span className="section-number">2</span>
            Select Target Role
          </h3>
          <div className="role-grid">
            {ROLES.map((role) => (
              <button
                key={role.id}
                className={`role-card glass-card ${selectedRole === role.id ? 'selected' : ''}`}
                onClick={() => setSelectedRole(role.id)}
                style={{ '--role-color': role.color }}
              >
                <div className="role-icon">{role.icon}</div>
                <h4 className="role-title">{role.title}</h4>
                <p className="role-desc">{role.desc}</p>
                {selectedRole === role.id && (
                  <div className="role-check">✓</div>
                )}
              </button>
            ))}
          </div>
        </section>

        {/* Error */}
        {error && (
          <div className="error-banner animate-scale-in">
            <span>⚠️</span> {error}
          </div>
        )}

        {/* Start Button */}
        <section className="start-section animate-fade-in-up" style={{ animationDelay: '0.35s' }}>
          <button
            className="btn btn-primary btn-lg start-btn"
            disabled={!canStart}
            onClick={handleStart}
          >
            {loading ? (
              <>
                <div className="spinner" />
                <span className="loading-text-cycle">{loadingText}</span>
              </>
            ) : (
              <>
                Start Interview →
              </>
            )}
          </button>
          {!file && !selectedRole && (
            <p className="start-hint">Upload your resume and select a role to begin</p>
          )}
        </section>

        {/* Features */}
        <section className="features animate-fade-in-up" style={{ animationDelay: '0.45s' }}>
          <div className="feature glass-card">
            <div className="feature-icon">📚</div>
            <h4>RAG-Powered</h4>
            <p>Questions grounded in ML textbook knowledge bases</p>
          </div>
          <div className="feature glass-card">
            <div className="feature-icon">🎯</div>
            <h4>Resume-Aware</h4>
            <p>Questions tailored to your skills and experience</p>
          </div>
          <div className="feature glass-card">
            <div className="feature-icon">🔄</div>
            <h4>Adaptive</h4>
            <p>Follow-up questions based on your responses</p>
          </div>
          <div className="feature glass-card">
            <div className="feature-icon">📊</div>
            <h4>Detailed Report</h4>
            <p>Comprehensive evaluation with per-topic scoring</p>
          </div>
        </section>
      </div>
    </div>
  )
}
