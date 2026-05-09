import { useState, useEffect } from 'react'
import { useParams, useLocation } from 'react-router-dom'
import { getInterviewSummary } from '../api/client'
import './ReportPage.css'

function ScoreRing({ score, label, color }) {
  const maxScore = 10
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / maxScore) * circumference

  return (
    <div className="score-card">
      <div className="score-ring">
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle className="score-ring-bg" cx="50" cy="50" r={radius} />
          <circle
            className="score-ring-progress"
            cx="50" cy="50" r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <span className="score-ring-value" style={{ color }}>
          {score}
        </span>
      </div>
      <span className="score-label">{label}</span>
    </div>
  )
}

export default function ReportPage() {
  const { sessionId } = useParams()
  const location = useLocation()
  const [report, setReport] = useState(location.state || null)
  const [loading, setLoading] = useState(!location.state)
  const [error, setError] = useState('')
  const [expandedQA, setExpandedQA] = useState(null)

  useEffect(() => {
    if (!report) {
      loadReport()
    }
  }, [sessionId])

  const loadReport = async () => {
    try {
      const data = await getInterviewSummary(sessionId)
      setReport(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load report')
    } finally {
      setLoading(false)
    }
  }

  const getRecommendationStyle = (rec) => {
    if (!rec) return {}
    const lower = rec.toLowerCase()
    if (lower.includes('strong hire')) return { bg: 'rgba(52, 211, 153, 0.1)', color: '#34d399', border: 'rgba(52, 211, 153, 0.3)' }
    if (lower.includes('hire') && !lower.includes('no')) return { bg: 'rgba(96, 165, 250, 0.1)', color: '#60a5fa', border: 'rgba(96, 165, 250, 0.3)' }
    if (lower.includes('lean hire')) return { bg: 'rgba(251, 191, 36, 0.1)', color: '#fbbf24', border: 'rgba(251, 191, 36, 0.3)' }
    if (lower.includes('no hire') || lower.includes('no')) return { bg: 'rgba(251, 113, 133, 0.1)', color: '#fb7185', border: 'rgba(251, 113, 133, 0.3)' }
    return { bg: 'rgba(129, 140, 248, 0.1)', color: '#818cf8', border: 'rgba(129, 140, 248, 0.3)' }
  }

  const getScoreColor = (score) => {
    if (score >= 8) return '#34d399'
    if (score >= 6) return '#60a5fa'
    if (score >= 4) return '#fbbf24'
    return '#fb7185'
  }

  if (loading) {
    return (
      <div className="report page">
        <div className="loading-area">
          <div className="spinner spinner-lg" />
          <p>Loading report...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="report page">
        <div className="error-banner">{error}</div>
      </div>
    )
  }

  if (!report) return null

  const recStyle = getRecommendationStyle(report.recommendation)

  return (
    <div className="report page">
      <div className="container">
        {/* Report Header */}
        <section className="report-header animate-fade-in-up">
          <div className="report-header-info">
            <h1>Interview Report</h1>
            <div className="report-meta">
              <span className="tag">{report.role}</span>
              <span className="report-date">
                {report.total_answered}/{report.total_questions} questions answered
              </span>
            </div>
          </div>
          <div
            className="recommendation-badge"
            style={{
              background: recStyle.bg,
              color: recStyle.color,
              borderColor: recStyle.border,
            }}
          >
            {report.recommendation || 'Pending Review'}
          </div>
        </section>

        {/* Score Cards */}
        <section className="scores-section animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <ScoreRing score={report.overall_score} label="Overall" color={getScoreColor(report.overall_score)} />
          <ScoreRing score={report.technical_depth_score} label="Technical Depth" color={getScoreColor(report.technical_depth_score)} />
          <ScoreRing score={report.communication_score} label="Communication" color={getScoreColor(report.communication_score)} />
          <ScoreRing score={report.relevance_score} label="Relevance" color={getScoreColor(report.relevance_score)} />
        </section>

        {/* Summary */}
        {report.summary && (
          <section className="report-section glass-card animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
            <h3 className="report-section-title">📋 Summary</h3>
            <p className="report-summary-text">{report.summary}</p>
          </section>
        )}

        {/* Strengths & Weaknesses */}
        <div className="sw-grid animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          {report.strengths?.length > 0 && (
            <div className="report-section glass-card">
              <h3 className="report-section-title" style={{ color: 'var(--color-success)' }}>
                💪 Strengths
              </h3>
              <ul className="sw-list">
                {report.strengths.map((s, i) => (
                  <li key={i} className="sw-item sw-strength">
                    <span className="sw-icon">✓</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {report.weaknesses?.length > 0 && (
            <div className="report-section glass-card">
              <h3 className="report-section-title" style={{ color: 'var(--color-warning)' }}>
                📌 Areas for Improvement
              </h3>
              <ul className="sw-list">
                {report.weaknesses.map((w, i) => (
                  <li key={i} className="sw-item sw-weakness">
                    <span className="sw-icon">→</span>
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Topic Performance */}
        {report.topic_performance && Object.keys(report.topic_performance).length > 0 && (
          <section className="report-section glass-card animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
            <h3 className="report-section-title">📊 Topic Performance</h3>
            <div className="topic-grid">
              {Object.entries(report.topic_performance).map(([topic, score]) => (
                <div key={topic} className="topic-bar-item">
                  <div className="topic-info">
                    <span className="topic-name">{topic}</span>
                    <span className="topic-score" style={{ color: getScoreColor(score) }}>{score}/10</span>
                  </div>
                  <div className="topic-bar">
                    <div
                      className="topic-fill"
                      style={{
                        width: `${(score / 10) * 100}%`,
                        background: getScoreColor(score),
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Q&A Log */}
        {report.qa_pairs?.length > 0 && (
          <section className="report-section animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
            <h3 className="report-section-title" style={{ marginBottom: 'var(--space-lg)' }}>
              💬 Interview Transcript
            </h3>
            <div className="qa-list stagger">
              {report.qa_pairs.map((qa, i) => (
                <div
                  key={i}
                  className={`qa-card glass-card ${expandedQA === i ? 'expanded' : ''}`}
                  onClick={() => setExpandedQA(expandedQA === i ? null : i)}
                >
                  <div className="qa-header">
                    <div className="qa-num">{i + 1}</div>
                    <div className="qa-info">
                      <p className="qa-question">{qa.question}</p>
                      <div className="qa-tags">
                        {qa.topic && <span className="tag">{qa.topic}</span>}
                        {qa.difficulty && <span className="tag">{qa.difficulty}</span>}
                        {qa.score != null && (
                          <span className="tag" style={{
                            color: getScoreColor(qa.score),
                            background: `${getScoreColor(qa.score)}15`,
                            borderColor: `${getScoreColor(qa.score)}30`,
                          }}>
                            {qa.score}/10
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="qa-toggle">{expandedQA === i ? '▼' : '▶'}</span>
                  </div>
                  {expandedQA === i && (
                    <div className="qa-body animate-fade-in">
                      <div className="qa-answer">
                        <strong>Answer:</strong>
                        <p>{qa.answer}</p>
                      </div>
                      {qa.feedback && (
                        <div className="qa-feedback">
                          <strong>Feedback:</strong>
                          <p>{qa.feedback}</p>
                        </div>
                      )}
                      {qa.context_source && (
                        <p className="qa-source">📚 Source: {qa.context_source}</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Detailed Feedback */}
        {report.detailed_feedback && (
          <section className="report-section glass-card animate-fade-in-up" style={{ animationDelay: '0.35s' }}>
            <h3 className="report-section-title">📝 Detailed Feedback</h3>
            <p className="report-feedback-text">{report.detailed_feedback}</p>
          </section>
        )}

        {/* Skills */}
        {report.candidate_skills?.length > 0 && (
          <section className="report-section glass-card animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            <h3 className="report-section-title">🛠️ Identified Skills</h3>
            <div className="skills-list">
              {report.candidate_skills.map((skill, i) => (
                <span key={i} className="tag">{skill}</span>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
