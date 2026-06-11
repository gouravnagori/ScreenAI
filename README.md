# 🧠 ScreenAI — AI-Powered Candidate Screening System

An intelligent, role-based candidate screening system that conducts structured technical interviews using **Retrieval-Augmented Generation (RAG)**. Questions are dynamically generated based on the candidate's resume, selected role, and domain-specific ML textbook knowledge bases.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange)
![Gemini](https://img.shields.io/badge/Gemini_AI-LLM-yellow?logo=google)

---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Setup Instructions](#-setup-instructions)
- [Knowledge Base Setup](#-knowledge-base-setup)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Key Design Decisions](#-key-design-decisions)
- [Project Structure](#-project-structure)

---

## ✨ Features

### Core Features
- **Resume Upload & Parsing** — PDF/text resume upload with automatic skill extraction, experience detection, and domain identification
- **Role-Based Screening** — Support for 4 roles: AI/ML Engineer, Data Scientist, Backend Engineer, Full-Stack Developer
- **RAG-Powered Questions** — Questions grounded in ML textbook knowledge bases, not generic templates
- **Voice-Enabled Interviewing** — Web Speech API integration for candidiate voice input and AI question playback
- **Anti-Cheat Proctoring** — Real-time tab-switch tracking with automated recruiter alerts
- **Visual Analytics Dashboard** — Recharts-powered Radar Charts for deep technical score visualization
- **HR Operations Dashboard** — Secure, password-protected portal (`/hr`) for recruiters to view all candidate sessions
- **PDF Report Generation** — One-click professional PDF downloads of candidate evaluations. 
- **Time Analytics** — Per-question and overall session time tracking

### Technical Highlights
- **Semantic Chunking** — 500-token chunks with 50-token overlap, preserving paragraph boundaries
- **Role-Filtered Retrieval** — ChromaDB metadata filtering ensures role-relevant content
- **Context Traceability** — Every question tracks which knowledge base content informed its generation
- **Modular Architecture** — Clean separation between API, services, and data layers
- **Markdown Processing** — Real-time formatting of LLM outputs using `react-markdown`
- **Native Browser APIs** — Zero-dependency Web Speech and Document Visibility API integration

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                    │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Landing  │→ │  Interview   │→ │   Report/Summary   │    │
│  │  Page     │  │  Page        │  │   Page             │    │
│  └──────────┘  └──────────────┘  └────────────────────┘    │
│                                           │                   │
│                                  ┌────────▼───────────┐    │
│                                  │   HR Dashboard     │    │
│                                  └────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────┴────────────────────────────────────┐
│                   Backend (FastAPI)                           │
│  ┌─────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │ Session  │  │  Interview   │  │  Knowledge Base     │    │
│  │ Router   │  │  Router      │  │  Router             │    │
│  └────┬─────┘  └──────┬───────┘  └──────────┬──────────┘    │
│       │               │                      │               │
│  ┌────┴───────────────┴──────────────────────┴──────────┐   │
│  │              Service Layer                            │   │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────────┐    │   │
│  │  │ Resume   │  │ Question  │  │  Evaluation    │    │   │
│  │  │ Parser   │  │ Service   │  │  Service       │    │   │
│  │  └──────────┘  └─────┬─────┘  └────────────────┘    │   │
│  │                      │                                │   │
│  │  ┌───────────────────┴────────────────────────────┐  │   │
│  │  │           RAG Service                           │  │   │
│  │  │  Query Construction → Retrieval → Generation    │  │   │
│  │  └───────────────────┬────────────────────────────┘  │   │
│  └──────────────────────┼────────────────────────────────┘   │
└─────────────────────────┼────────────────────────────────────┘
                          │
┌─────────────────────────┴────────────────────────────────────┐
│                     Data Layer                                │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │  SQLite    │  │  ChromaDB    │  │  ML Textbook     │     │
│  │  Database  │  │  Vector DB   │  │  PDFs            │     │
│  └────────────┘  └──────────────┘  └──────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | React 18 + Vite | Premium dark-mode UI |
| **Backend** | FastAPI (Python) | REST API & business logic |
| **LLM** | Google Gemini 2.5 Flash | Question generation & evaluation |
| **Vector DB** | ChromaDB | Knowledge base storage & retrieval |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Semantic text embeddings |
| **Database** | SQLite | Session, Q&A, evaluation persistence |
| **PDF Parsing** | pdfplumber | Resume & textbook text extraction |
| **HTTP Client** | Axios | Frontend-backend communication |
| **Routing** | React Router v6 | Client-side navigation |

---

## 🚀 Setup Instructions

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and npm
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/apikey))

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/intelligent-hiring-assistant.git
cd intelligent-hiring-assistant
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

### 3. Setup Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Setup Frontend

```bash
cd frontend
npm install
```

### 5. Knowledge Base (Pre-loaded)

The repository includes **3 comprehensive ML knowledge base files** in `backend/knowledge_base/books/` covering:

| File | Content | Topics |
|------|---------|--------|
| `ml_fundamentals_mitchell.txt` | Machine Learning Fundamentals | Decision Trees, Neural Networks, SVMs, Bayesian Learning, Ensemble Methods |
| `deep_learning_burkov.txt` | Deep Learning & Neural Networks | CNNs, RNNs, Transformers, Attention, GANs, Autoencoders |
| `applied_ml_algorithms.txt` | Applied ML & Data Science | Preprocessing, Evaluation Metrics, Clustering, NLP, Recommender Systems |

These are **automatically ingested** on server startup into ChromaDB for semantic retrieval.

> **Optional**: You can also add your own PDF textbooks to `backend/knowledge_base/books/` for additional domain coverage. The system supports both `.txt` and `.pdf` formats.

---

## ▶️ Running the Application

### Start Backend (Terminal 1)

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📡 API Documentation

### Session Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/session/start` | POST | Upload resume + role → start interview |
| `/api/session/{id}` | GET | Get session status |

### Interview Lifecycle

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/interview/{id}/question` | GET | Get next unanswered question |
| `/api/interview/{id}/answer` | POST | Submit answer (with adaptive follow-up) |
| `/api/interview/{id}/complete` | POST | Complete interview → generate evaluation |
| `/api/interview/{id}/summary` | GET | Get evaluation report |

### Knowledge Base

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/knowledge/status` | GET | Check ingestion status |
| `/api/knowledge/ingest` | POST | Trigger book ingestion |
| `/api/health` | GET | Health check |

---

## 🧩 Key Design Decisions

### RAG Pipeline
- **ChromaDB over FAISS**: Chose ChromaDB for built-in persistence, metadata filtering, and no external server requirement
- **all-MiniLM-L6-v2 embeddings**: Fast CPU inference, good semantic quality — no GPU needed
- **500-token chunks with 50-token overlap**: Balances context preservation (larger chunks) with retrieval precision (smaller chunks)
- **Paragraph-boundary chunking**: Preserves semantic coherence unlike fixed-size splitting

### Question Generation
- **Context-grounded**: Every question is generated using retrieved textbook content, not generic templates
- **Difficulty calibration**: Mix of easy/medium/hard based on role and experience
- **Source traceability**: Each question records which knowledge base content informed it

### Architecture
- **Modular service layer**: Resume parsing, RAG, question generation, and evaluation are independent services
- **Session-based design**: Each interview is a complete session with full data lifecycle
- **Separation of concerns**: Routers handle HTTP, services handle logic, database handles persistence

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py                     # FastAPI entry point
│   ├── config.py                   # Environment configuration
│   ├── requirements.txt            # Python dependencies
│   ├── models/
│   │   ├── database.py             # SQLite schema & CRUD
│   │   └── schemas.py              # Pydantic request/response models
│   ├── routers/
│   │   ├── session.py              # Session endpoints
│   │   ├── interview.py            # Interview lifecycle endpoints
│   │   └── knowledge.py            # Knowledge base endpoints
│   ├── services/
│   │   ├── resume_parser.py        # PDF parsing & skill extraction
│   │   ├── rag_service.py          # RAG pipeline (ingest/retrieve)
│   │   ├── llm_service.py          # Gemini LLM integration
│   │   ├── question_service.py     # Question generation orchestrator
│   │   └── evaluation_service.py   # Evaluation & scoring
│   └── knowledge_base/
│       └── books/                  # ML knowledge base (.txt included, .pdf gitignored)
│           ├── ml_fundamentals_mitchell.txt
│           ├── deep_learning_burkov.txt
│           └── applied_ml_algorithms.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.js           # Axios API client
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx     # Resume upload + role selection
│   │   │   ├── InterviewPage.jsx   # Q&A interview flow with voice/proctoring
│   │   │   ├── ReportPage.jsx      # Evaluation report with PDF download
│   │   │   └── HRDashboard.jsx     # Secure recruiter dashboard
│   │   └── components/
│   │       └── Header.jsx          # Navigation header
│   ├── index.html
│   └── package.json
├── .env.example
├── .gitignore
└── README.md
```

---

## 🌐 Deployment (Render)

### Backend
1. Create a new **Web Service** on Render
2. Set **Root Directory**: `backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `GEMINI_API_KEY=your_key`

### Frontend
1. Create a new **Static Site** on Render (or use Vercel)
2. Set **Root Directory**: `frontend`
3. **Build Command**: `npm install && npm run build`
4. **Publish Directory**: `dist`
5. Add environment variable: `VITE_API_URL=https://your-backend-url.onrender.com/api` (Replace with your actual deployed backend URL)

---

## 📄 License

This project was built as part of the PGAGI AI/ML & Backend Engineering Intern Assignment.
