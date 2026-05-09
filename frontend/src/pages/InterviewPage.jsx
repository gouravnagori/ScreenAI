import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { getNextQuestion, submitAnswer, completeInterview } from '../api/client'
import './InterviewPage.css'

export default function InterviewPage() {
  const { sessionId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const sessionData = location.state || {}

  const [currentQuestion, setCurrentQuestion] = useState(sessionData.first_question || null)
  const [answerText, setAnswerText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [completing, setCompleting] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState([])
  const [totalQuestions, setTotalQuestions] = useState(sessionData.total_questions || 5)
  const [answered, setAnswered] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  // Load first question if navigated directly
  useEffect(() => {
    if (!currentQuestion && sessionId) {
      loadNextQuestion()
    }
  }, [sessionId])

  const loadNextQuestion = async () => {
    try {
      const q = await getNextQuestion(sessionId)
      setCurrentQuestion(q)
      setTotalQuestions(q.total_questions)
    } catch (err) {
      if (err.response?.status === 404) {
        setIsComplete(true)
      } else {
        setError(err.response?.data?.detail || 'Failed to load question')
      }
    }
  }

  const handleSubmitAnswer = async () => {
    if (!answerText.trim() || submitting) return
    setSubmitting(true)
    setError('')

    try {
      const result = await submitAnswer(sessionId, currentQuestion.question_id, answerText.trim())

      // Add to history
      setHistory(prev => [...prev, {
        question: currentQuestion,
        answer: answerText.trim()
      }])
      setAnswered(prev => prev + 1)
      setAnswerText('')

      if (result.is_complete || !result.next_question) {
        setIsComplete(true)
        setCurrentQuestion(null)
      } else {
        setCurrentQuestion(result.next_question)
        setTotalQuestions(result.next_question.total_questions)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit answer')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCompleteInterview = async () => {
    setCompleting(true)
    setError('')
    try {
      const summary = await completeInterview(sessionId)
      navigate(`/report/${sessionId}`, { state: summary })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate evaluation')
      setCompleting(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmitAnswer()
    }
  }

  const progress = totalQuestions > 0 ? (answered / totalQuestions) * 100 : 0

  const difficultyColor = {
    easy: 'var(--color-success)',
    medium: 'var(--color-warning)',
    hard: 'var(--color-danger)',
  }

  return (
    <div className="interview page">
      <div className="interview-layout">
        {/* Sidebar */}
        <aside className="interview-sidebar glass-card">
          <div className="sidebar-section">
            <h4 className="sidebar-title">Session Info</h4>
            <div className="sidebar-info">
              <div className="info-row">
                <span className="info-label">Role</span>
                <span className="info-value tag">{sessionData.role || 'N/A'}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Progress</span>
                <span className="info-value">{answered}/{totalQuestions}</span>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="sidebar-section">
            <div className="progress-bar-container">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <span className="progress-label">{Math.round(progress)}% Complete</span>
            </div>
          </div>

          {/* Extracted Skills */}
          {sessionData.extracted_skills?.length > 0 && (
            <div className="sidebar-section">
              <h4 className="sidebar-title">Detected Skills</h4>
              <div className="skills-list">
                {sessionData.extracted_skills.slice(0, 12).map((skill, i) => (
                  <span key={i} className="tag">{skill}</span>
                ))}
                {sessionData.extracted_skills.length > 12 && (
                  <span className="tag tag-more">+{sessionData.extracted_skills.length - 12}</span>
                )}
              </div>
            </div>
          )}

          {/* Q&A History */}
          {history.length > 0 && (
            <div className="sidebar-section">
              <h4 className="sidebar-title">Answered</h4>
              <div className="history-list">
                {history.map((item, i) => (
                  <div key={i} className="history-item">
                    <span className="history-num">{i + 1}</span>
                    <span className="history-topic">{item.question.topic || 'Question'}</span>
                    <span className="history-check">✓</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Main Interview Area */}
        <main className="interview-main">
          {currentQuestion && !isComplete ? (
            <div className="question-area animate-fade-in-up" key={currentQuestion.question_id}>
              {/* Question Card */}
              <div className="question-card glass-card">
                <div className="question-header">
                  <div className="question-meta">
                    <span className="question-number">
                      Question {currentQuestion.question_number} of {totalQuestions}
                    </span>
                    <div className="question-tags">
                      {currentQuestion.topic && (
                        <span className="tag">{currentQuestion.topic}</span>
                      )}
                      <span
                        className="tag"
                        style={{
                          background: `${difficultyColor[currentQuestion.difficulty] || 'var(--accent-primary)'}15`,
                          color: difficultyColor[currentQuestion.difficulty] || 'var(--accent-primary)',
                          borderColor: `${difficultyColor[currentQuestion.difficulty] || 'var(--accent-primary)'}30`,
                        }}
                      >
                        {currentQuestion.difficulty || 'medium'}
                      </span>
                    </div>
                  </div>
                  {currentQuestion.context_source && (
                    <p className="question-source">
                      📚 Based on: {currentQuestion.context_source}
                    </p>
                  )}
                </div>

                <div className="question-body">
                  <p className="question-text">{currentQuestion.question_text}</p>
                </div>
              </div>

              {/* Answer Input */}
              <div className="answer-area">
                <textarea
                  className="answer-input"
                  placeholder="Type your answer here... (Ctrl+Enter to submit)"
                  value={answerText}
                  onChange={(e) => setAnswerText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={submitting}
                  rows={6}
                />
                <div className="answer-footer">
                  <span className="char-count">
                    {answerText.length} / 5000
                  </span>
                  <button
                    className="btn btn-primary"
                    onClick={handleSubmitAnswer}
                    disabled={!answerText.trim() || submitting}
                  >
                    {submitting ? (
                      <>
                        <div className="spinner" /> Submitting...
                      </>
                    ) : (
                      'Submit Answer →'
                    )}
                  </button>
                </div>
              </div>
            </div>
          ) : isComplete ? (
            <div className="complete-area animate-scale-in">
              <div className="complete-card glass-card">
                <div className="complete-icon">🎉</div>
                <h2>Interview Complete!</h2>
                <p>
                  You've answered all {answered} questions. Click below to generate
                  your comprehensive evaluation report.
                </p>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleCompleteInterview}
                  disabled={completing}
                >
                  {completing ? (
                    <>
                      <div className="spinner" /> Generating Evaluation...
                    </>
                  ) : (
                    'Generate Report →'
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="loading-area">
              <div className="spinner spinner-lg" />
              <p>Loading question...</p>
            </div>
          )}

          {error && (
            <div className="error-banner animate-scale-in">
              <span>⚠️</span> {error}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
