import { useState, useEffect } from 'react'
import { useParams, useLocation } from 'react-router-dom'
import { getInterviewSummary } from '../api/client'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts'
import ReactMarkdown from 'react-markdown'
import { AlertTriangle, Download, Clock } from 'lucide-react'
import html2pdf from 'html2pdf.js'
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
  const warnings = report.warnings || 0

  // Prepare data for Radar Chart
  const radarData = [
    { subject: 'Overall', A: report.overall_score || 0, fullMark: 10 },
    { subject: 'Technical', A: report.technical_depth_score || 0, fullMark: 10 },
    { subject: 'Communication', A: report.communication_score || 0, fullMark: 10 },
    { subject: 'Relevance', A: report.relevance_score || 0, fullMark: 10 },
  ]
  
  if (report.topic_performance) {
    Object.entries(report.topic_performance).forEach(([topic, score]) => {
      // Shorten long topic names for the chart
      const shortTopic = topic.length > 15 ? topic.substring(0, 15) + '...' : topic
      radarData.push({ subject: shortTopic, A: score, fullMark: 10 })
    })
  }

  const formatTime = (seconds) => {
    if (!seconds) return '00:00';
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleDownloadPDF = () => {
    const element = document.getElementById('pdf-report-content');
    const opt = {
      margin:       0.3,
      filename:     `ScreenAI_Report_${report.role.replace(/[^a-z0-9]/gi, '_')}.pdf`,
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true, backgroundColor: '#0d0f1a' },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(element).save();
  };

  return (
    <div className="report page">
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
          <button className="btn btn-secondary" onClick={handleDownloadPDF} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Download size={18} /> Download PDF
          </button>
        </div>
        
        <div id="pdf-report-content">
          {/* Report Header */}
        <section className="report-header animate-fade-in-up">
          <div className="report-header-info">
            <h1>Interview Report</h1>
            <div className="report-meta">
              <span className="tag">{report.role}</span>
              <span className="report-date">
                {report.total_answered}/{report.total_questions} questions answered
              </span>
              <span className="tag" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                <Clock size={14} style={{ marginRight: '4px' }} />
                {formatTime(report.total_time_taken_seconds)}
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

        {warnings > 0 && (
          <div className="report-section glass-card animate-fade-in-up" style={{ borderColor: 'rgba(251, 113, 133, 0.3)', background: 'rgba(251, 113, 133, 0.05)', animationDelay: '0.05s' }}>
            <h3 className="report-section-title" style={{ color: '#fb7185', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={20} /> Proctoring Flags Detected
            </h3>
            <p style={{ margin: 0, opacity: 0.9 }}>We detected <strong>{warnings}</strong> tab switches or window exits during the assessment. This has been logged for the recruiter's review.</p>
          </div>
        )}

        {/* Analytics Dashboard (Radar Chart + Scores) */}
        <section className="analytics-section animate-fade-in-up" style={{ animationDelay: '0.1s', display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: 'var(--space-xl)' }}>
          <div className="radar-chart-container glass-card" style={{ flex: '1 1 400px', height: '380px', padding: '24px', display: 'flex', flexDirection: 'column' }}>
            <h3 className="report-section-title" style={{ marginBottom: '10px' }}>📊 Visual Analytics</h3>
            <div style={{ flex: 1, minHeight: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.15)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.8)', fontSize: 13, fontWeight: 500 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
                  <Radar name="Score" dataKey="A" stroke="#818cf8" fill="#818cf8" fillOpacity={0.5} strokeWidth={2} />
                  <RechartsTooltip contentStyle={{ backgroundColor: '#1e1e2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="scores-grid" style={{ flex: '1 1 300px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', alignContent: 'start' }}>
            <ScoreRing score={report.overall_score} label="Overall" color={getScoreColor(report.overall_score)} />
            <ScoreRing score={report.technical_depth_score} label="Technical Depth" color={getScoreColor(report.technical_depth_score)} />
            <ScoreRing score={report.communication_score} label="Communication" color={getScoreColor(report.communication_score)} />
            <ScoreRing score={report.relevance_score} label="Relevance" color={getScoreColor(report.relevance_score)} />
          </div>
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
                        <span className="tag" style={{ background: 'transparent', borderColor: 'var(--border-subtle)', color: 'var(--text-muted)' }}>
                          <Clock size={12} style={{ marginRight: '4px' }} />
                          {formatTime(qa.time_taken_seconds)}
                        </span>
                      </div>
                    </div>
                    <span className="qa-toggle">{expandedQA === i ? '▼' : '▶'}</span>
                  </div>
                  {expandedQA === i && (
                    <div className="qa-body animate-fade-in">
                      <div className="qa-answer">
                        <strong>Answer:</strong>
                        <div className="markdown-body-override" style={{ marginTop: '8px' }}>
                          <ReactMarkdown>{qa.answer}</ReactMarkdown>
                        </div>
                      </div>
                      {qa.feedback && (
                        <div className="qa-feedback" style={{ marginTop: '16px' }}>
                          <strong>Feedback:</strong>
                          <div className="markdown-body-override" style={{ marginTop: '8px' }}>
                            <ReactMarkdown>{qa.feedback}</ReactMarkdown>
                          </div>
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
    </div>
  )
}
