import { useState, useEffect, useRef } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { getNextQuestion, submitAnswer, completeInterview } from '../api/client'
import ReactMarkdown from 'react-markdown'
import { Mic, Square, Volume2, VolumeX, AlertTriangle } from 'lucide-react'
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

  // Extension States
  const [warnings, setWarnings] = useState(0)
  const [isRecording, setIsRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [questionStartTime, setQuestionStartTime] = useState(Date.now())
  const recognitionRef = useRef(null)

  // Load first question if navigated directly
  useEffect(() => {
    if (!currentQuestion && sessionId) {
      loadNextQuestion()
    }
  }, [sessionId])

  // Anti-Cheat / Proctoring: Track tab switches
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && !isComplete) {
        setWarnings(w => w + 1)
        setTimeout(() => alert('⚠️ PROCTORING WARNING: Tab switch detected. This action has been logged.'), 100)
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [isComplete])

  // Speech Recognition Setup
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      const recog = new SpeechRecognition()
      recog.continuous = true
      recog.interimResults = true
      
      recog.onresult = (event) => {
        let finalTranscript = ''
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript + ' '
          }
        }
        if (finalTranscript) {
          setAnswerText(prev => (prev + ' ' + finalTranscript).trim())
        }
      }
      recog.onerror = (event) => {
        console.error('Speech recognition error', event.error)
        setIsRecording(false)
      }
      recog.onend = () => {
        setIsRecording(false)
      }
      recognitionRef.current = recog
    }
  }, [])

  const toggleRecording = () => {
    if (!recognitionRef.current) return alert('Speech recognition not supported in this browser.')
    if (isRecording) {
      recognitionRef.current.stop()
    } else {
      recognitionRef.current.start()
      setIsRecording(true)
    }
  }

  const toggleSpeech = (text) => {
    if (isPlaying) {
      window.speechSynthesis.cancel()
      setIsPlaying(false)
      return
    }
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.onend = () => setIsPlaying(false)
    setIsPlaying(true)
    window.speechSynthesis.speak(utterance)
  }

  const loadNextQuestion = async () => {
    try {
      const q = await getNextQuestion(sessionId)
      setCurrentQuestion(q)
      setTotalQuestions(q.total_questions)
      setQuestionStartTime(Date.now())
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

    // Stop any playing audio
    if (isPlaying) {
      window.speechSynthesis.cancel()
      setIsPlaying(false)
    }
    
    // Stop recording if active
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop()
    }

    try {
      const timeTaken = Math.floor((Date.now() - questionStartTime) / 1000)
      const result = await submitAnswer(sessionId, currentQuestion.question_id, answerText.trim(), timeTaken)

      // Add to history
      setHistory(prev => [...prev, {
        question: currentQuestion,
        answer: answerText.trim(),
        time_taken_seconds: timeTaken
      }])
      setAnswered(prev => prev + 1)
      setAnswerText('')

      if (result.is_complete || !result.next_question) {
        setIsComplete(true)
        setCurrentQuestion(null)
      } else {
        setCurrentQuestion(result.next_question)
        setTotalQuestions(result.next_question.total_questions)
        setQuestionStartTime(Date.now())
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
      navigate(`/report/${sessionId}`, { state: { ...summary, warnings } })
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
              {warnings > 0 && (
                <div className="info-row warning-row" style={{ color: '#fb7185', marginTop: '8px' }}>
                  <span className="info-label"><AlertTriangle size={14} style={{ marginRight: '4px', verticalAlign: 'text-bottom' }}/> Warnings</span>
                  <span className="info-value warning-value">{warnings}</span>
                </div>
              )}
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
                  <div className="question-actions" style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
                     <button 
                       className="btn btn-icon" 
                       onClick={() => toggleSpeech(currentQuestion.question_text)}
                       title={isPlaying ? "Stop Reading" : "Read Question"}
                       style={{ padding: '8px', background: 'var(--bg-tertiary)', borderRadius: '8px', border: '1px solid var(--border-color)', color: isPlaying ? 'var(--accent-primary)' : 'inherit', cursor: 'pointer' }}
                     >
                       {isPlaying ? <VolumeX size={18} /> : <Volume2 size={18} />}
                     </button>
                  </div>
                  <div className="question-text" style={{ fontSize: '1.1rem', lineHeight: '1.6' }}>
                    <ReactMarkdown>{currentQuestion.question_text}</ReactMarkdown>
                  </div>
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
                <div className="answer-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                  <div className="answer-tools" style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                    <button 
                      className="btn btn-icon"
                      onClick={toggleRecording}
                      title={isRecording ? "Stop Recording" : "Start Recording"}
                      style={{ 
                        padding: '8px 12px', 
                        background: isRecording ? 'rgba(251, 113, 133, 0.1)' : 'var(--bg-tertiary)', 
                        borderRadius: '8px', 
                        border: `1px solid ${isRecording ? 'rgba(251, 113, 133, 0.3)' : 'var(--border-color)'}`, 
                        color: isRecording ? '#fb7185' : 'inherit',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      {isRecording ? <Square size={16} /> : <Mic size={16} />}
                      {isRecording ? "Stop" : "Speak"}
                    </button>
                    <span className="char-count" style={{ opacity: 0.6, fontSize: '0.9rem' }}>
                      {answerText.length} / 5000
                    </span>
                  </div>
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
