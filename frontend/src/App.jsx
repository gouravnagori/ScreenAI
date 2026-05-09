import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import InterviewPage from './pages/InterviewPage'
import ReportPage from './pages/ReportPage'
import Header from './components/Header'
import './App.css'

function App() {
  return (
    <div className="app">
      <Header />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/interview/:sessionId" element={<InterviewPage />} />
          <Route path="/report/:sessionId" element={<ReportPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
