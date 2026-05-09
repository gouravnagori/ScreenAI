import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minutes — question generation can take time
  headers: {
    'Accept': 'application/json',
  },
});

// ─── Session API ────────────────────────────────────────

export async function startSession(resumeFile, role) {
  const formData = new FormData();
  formData.append('resume', resumeFile);
  formData.append('role', role);

  const response = await client.post('/session/start', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function getSessionStatus(sessionId) {
  const response = await client.get(`/session/${sessionId}`);
  return response.data;
}

// ─── Interview API ──────────────────────────────────────

export async function getNextQuestion(sessionId) {
  const response = await client.get(`/interview/${sessionId}/question`);
  return response.data;
}

export async function submitAnswer(sessionId, questionId, answerText) {
  const response = await client.post(`/interview/${sessionId}/answer`, {
    question_id: questionId,
    answer_text: answerText,
  });
  return response.data;
}

export async function completeInterview(sessionId) {
  const response = await client.post(`/interview/${sessionId}/complete`);
  return response.data;
}

export async function getInterviewSummary(sessionId) {
  const response = await client.get(`/interview/${sessionId}/summary`);
  return response.data;
}

// ─── Knowledge Base API ─────────────────────────────────

export async function getKnowledgeStatus() {
  const response = await client.get('/knowledge/status');
  return response.data;
}

export async function ingestKnowledgeBase() {
  const response = await client.post('/knowledge/ingest');
  return response.data;
}

// ─── Health Check ───────────────────────────────────────

export async function healthCheck() {
  const response = await client.get('/health');
  return response.data;
}

export default client;
