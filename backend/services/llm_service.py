"""
LLM Service — Google Gemini API integration.
Handles all LLM interactions: question generation, answer evaluation, and summary generation.
Includes retry logic with model fallback for rate limit resilience.
"""

import json
import time
import google.generativeai as genai
from config import settings

_model = None
_configured = False

# Fallback model chain — if primary model quota is exhausted, try alternatives
MODEL_FALLBACK_CHAIN = [
    settings.LLM_MODEL,
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


def _get_model(model_name: str = None):
    """Lazy-initialize the Gemini model."""
    global _model, _configured
    if not _configured:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True
    
    name = model_name or settings.LLM_MODEL
    return genai.GenerativeModel(
        model_name=name,
        generation_config={
            "temperature": settings.LLM_TEMPERATURE,
            "top_p": 0.9,
            "max_output_tokens": settings.LLM_MAX_TOKENS,
        },
    )


def _call_llm(prompt: str, max_retries: int = 3) -> str:
    """Call LLM with retry logic and model fallback."""
    for model_name in MODEL_FALLBACK_CHAIN:
        for attempt in range(max_retries):
            try:
                model = _get_model(model_name)
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "ResourceExhausted" in error_str:
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt * 5  # 5s, 10s, 20s
                        print(f"  [RETRY] Rate limited on {model_name}, waiting {wait}s (attempt {attempt+1})")
                        time.sleep(wait)
                    else:
                        print(f"  [WARN] {model_name} quota exhausted, trying next model...")
                        break  # Try next model in chain
                else:
                    print(f"  [ERR] LLM error ({model_name}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        break
    raise RuntimeError("All LLM models exhausted or errored")


def generate_questions(
    skills: list[str],
    role: str,
    experience: str,
    rag_contexts: list[dict],
    num_questions: int = 5,
) -> list[dict]:
    """
    Generate interview questions using RAG-retrieved context.
    
    Args:
        skills: Extracted skills from resume.
        role: Target role.
        experience: Experience level description.
        rag_contexts: Retrieved knowledge base chunks with source info.
        num_questions: Number of questions to generate.
        
    Returns:
        List of question dicts with text, topic, difficulty, and source.
    """
    # Format RAG context for the prompt
    context_text = ""
    for i, ctx in enumerate(rag_contexts[:8], 1):
        source = ctx.get("source", "Knowledge Base")
        context_text += f"\n--- Context {i} (Source: {source}) ---\n{ctx['text'][:800]}\n"

    prompt = f"""You are an expert technical interviewer. Generate exactly {num_questions} interview questions for a candidate.

CANDIDATE PROFILE:
- Target Role: {role}
- Skills: {', '.join(skills) if skills else 'Not specified'}
- Experience: {experience}

KNOWLEDGE BASE CONTEXT (use this to ground your questions — do NOT ask generic questions):
{context_text}

QUESTION GENERATION RULES:
1. Generate exactly {num_questions} questions
2. Each question MUST be grounded in the provided context — reference specific concepts from the knowledge base
3. Questions should be relevant to the candidate's skills AND the target role
4. Mix difficulty levels: 1 easy, 2 medium, 2 hard
5. Include different question types:
   - Conceptual understanding (explain a concept)
   - Applied/scenario-based (solve a practical problem)
   - Analytical (compare approaches, discuss trade-offs)
6. Questions should NOT be answerable with a simple yes/no
7. Each question should be 1-3 sentences
8. Avoid textbook definitions — ask questions that test understanding

RESPOND WITH ONLY a valid JSON array. No markdown, no code fences, no extra text.
Each element should have:
- "question_text": the question string
- "topic": the ML/CS topic being tested
- "difficulty": "easy", "medium", or "hard"
- "context_source": brief description of which knowledge base content informed this question

Example format:
[
  {{
    "question_text": "Given a dataset with high dimensionality...",
    "topic": "Dimensionality Reduction",
    "difficulty": "medium",
    "context_source": "Chapter on feature selection and PCA"
  }}
]
"""

    try:
        text = _call_llm(prompt)

        # Clean markdown fences
        text = text.replace("```json", "").replace("```", "").strip()

        questions = json.loads(text)
        if isinstance(questions, list):
            return questions[:num_questions]
    except json.JSONDecodeError:
        # Try to extract JSON array from response
        import re
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            try:
                return json.loads(match.group())[:num_questions]
            except Exception:
                pass
    except Exception as e:
        print(f"Question generation error: {e}")

    # Fallback questions
    return _fallback_questions(skills, role, num_questions)


def generate_adaptive_followup(
    previous_question: str,
    answer: str,
    rag_contexts: list[dict],
    role: str,
) -> dict | None:
    """
    Generate an adaptive follow-up question based on the candidate's answer.
    
    Returns:
        A question dict, or None if no follow-up is warranted.
    """
    context_text = ""
    for ctx in rag_contexts[:3]:
        context_text += f"\n{ctx['text'][:500]}\n"

    prompt = f"""Analyze this interview exchange and decide if a follow-up question would be valuable.

ROLE: {role}
PREVIOUS QUESTION: {previous_question}
CANDIDATE'S ANSWER: {answer}

RELEVANT CONTEXT:
{context_text}

If the answer shows:
- Partial understanding → Ask a clarifying question to dig deeper
- Strong understanding → Ask a more challenging follow-up
- Misconception → Ask a question that guides them toward the correct understanding
- Complete/excellent answer → Return null (no follow-up needed)

If a follow-up is appropriate, respond with JSON:
{{"question_text": "...", "topic": "...", "difficulty": "...", "context_source": "follow-up", "is_followup": true}}

If no follow-up is needed, respond with exactly: null
"""

    try:
        text = _call_llm(prompt)
        text = text.replace("```json", "").replace("```", "").strip()

        if text.lower() == "null" or text.lower() == "none":
            return None

        return json.loads(text)
    except Exception:
        return None


def generate_evaluation(
    qa_pairs: list[dict],
    role: str,
    skills: list[str],
    experience: str,
) -> dict:
    """
    Generate a comprehensive evaluation of the interview session.
    
    Args:
        qa_pairs: List of {question, answer, topic, difficulty, context_source}
        role: Target role
        skills: Candidate's skills
        experience: Experience level
        
    Returns:
        Evaluation dict with scores, summary, strengths, weaknesses, etc.
    """
    qa_text = ""
    for i, pair in enumerate(qa_pairs, 1):
        qa_text += f"""
--- Question {i} ---
Topic: {pair.get('topic', 'General')}
Difficulty: {pair.get('difficulty', 'medium')}
Q: {pair['question_text']}
A: {pair.get('answer_text', 'No answer provided')}
"""

    prompt = f"""You are a senior technical hiring manager. Evaluate this interview session comprehensively.

CANDIDATE PROFILE:
- Target Role: {role}
- Skills: {', '.join(skills) if skills else 'Not specified'}
- Experience: {experience}

INTERVIEW TRANSCRIPT:
{qa_text}

Generate a thorough evaluation. Score each dimension from 0-10.

RESPOND WITH ONLY valid JSON (no markdown, no code fences):
{{
    "overall_score": <0-10>,
    "technical_depth_score": <0-10>,
    "communication_score": <0-10>,
    "relevance_score": <0-10>,
    "summary": "2-3 sentence professional summary of the candidate's performance",
    "strengths": ["strength 1 — evidence-based", "strength 2 — evidence-based"],
    "weaknesses": ["area for improvement 1", "area for improvement 2"],
    "recommendation": "Strong Hire | Hire | Lean Hire | Lean No Hire | No Hire",
    "detailed_feedback": "A paragraph of constructive, specific feedback",
    "per_question_scores": [
        {{"question_number": 1, "score": <0-10>, "feedback": "brief assessment"}},
        ...
    ],
    "topic_performance": {{"topic_name": <0-10 score>, ...}}
}}

SCORING GUIDE:
- 9-10: Exceptional — deep understanding, creative solutions
- 7-8: Strong — solid understanding with minor gaps
- 5-6: Moderate — basic understanding, missing depth
- 3-4: Below Average — significant knowledge gaps
- 1-2: Weak — fundamental misunderstandings
- 0: No answer or completely irrelevant

Be fair but rigorous. Base all assessments on actual answers, not assumptions.
"""

    try:
        text = _call_llm(prompt)
        text = text.replace("```json", "").replace("```", "").strip()

        evaluation = json.loads(text)
        return evaluation
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    except Exception as e:
        print(f"Evaluation generation error: {e}")

    # Fallback evaluation
    return {
        "overall_score": 5,
        "technical_depth_score": 5,
        "communication_score": 5,
        "relevance_score": 5,
        "summary": "Evaluation could not be generated automatically. Manual review recommended.",
        "strengths": ["Participated in the interview process"],
        "weaknesses": ["Automated evaluation encountered an error"],
        "recommendation": "Review Required",
        "detailed_feedback": "The automated evaluation could not be completed. Please review the Q&A transcript directly.",
        "per_question_scores": [],
        "topic_performance": {},
    }


def _fallback_questions(skills: list[str], role: str, count: int) -> list[dict]:
    """Generate fallback questions when LLM fails."""
    skill_str = skills[0] if skills else 'your technical skills'
    base_questions = [
        {
            "question_text": f"Describe a challenging technical problem you solved using {skill_str}. What approach did you take and what was the outcome?",
            "topic": "Problem Solving",
            "difficulty": "medium",
            "context_source": "Fallback — general",
        },
        {
            "question_text": "Explain the bias-variance tradeoff in machine learning. How does it affect model selection and what strategies can you use to find the right balance?",
            "topic": "ML Fundamentals",
            "difficulty": "medium",
            "context_source": "Fallback — ML fundamentals",
        },
        {
            "question_text": "What is overfitting and what strategies would you use to prevent it? Discuss at least three different regularization techniques.",
            "topic": "Model Training",
            "difficulty": "easy",
            "context_source": "Fallback — ML fundamentals",
        },
        {
            "question_text": "Compare and contrast supervised, unsupervised, and reinforcement learning. Give a practical use case for each paradigm.",
            "topic": "Learning Paradigms",
            "difficulty": "easy",
            "context_source": "Fallback — ML fundamentals",
        },
        {
            "question_text": "Explain how gradient descent works in training neural networks. What is backpropagation and how does it compute gradients efficiently?",
            "topic": "Neural Networks",
            "difficulty": "hard",
            "context_source": "Fallback — deep learning",
        },
        {
            "question_text": "What are the key differences between Random Forests and Gradient Boosting? When would you choose one over the other?",
            "topic": "Ensemble Methods",
            "difficulty": "medium",
            "context_source": "Fallback — ML algorithms",
        },
        {
            "question_text": "Explain the attention mechanism in Transformers. Why was it a breakthrough compared to RNN-based sequence models?",
            "topic": "Deep Learning",
            "difficulty": "hard",
            "context_source": "Fallback — deep learning",
        },
        {
            "question_text": "Walk through how you would evaluate a classification model on an imbalanced dataset. Which metrics would you use and why?",
            "topic": "Model Evaluation",
            "difficulty": "medium",
            "context_source": "Fallback — applied ML",
        },
        {
            "question_text": "Design a machine learning pipeline for a real-world problem in your domain. Walk through the steps from data collection to model deployment and monitoring.",
            "topic": "System Design",
            "difficulty": "hard",
            "context_source": "Fallback — applied ML",
        },
    ]
    return base_questions[:count]
