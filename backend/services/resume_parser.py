"""
Resume Parser — Extracts structured information from PDF and text resumes.
Uses pdfplumber for PDF parsing and regex/keyword matching for skill extraction.
"""

import re
import pdfplumber
from io import BytesIO


# ─── Known Skills Database ───────────────────────────────
KNOWN_SKILLS = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "perl", "dart", "lua", "julia", "sql", "bash",
        "shell", "powershell", "html", "css", "sass", "scss",
    ],
    "frameworks": [
        "react", "angular", "vue", "svelte", "next.js", "nextjs", "nuxt",
        "django", "flask", "fastapi", "express", "spring", "spring boot",
        "rails", "laravel", "asp.net", ".net", "nestjs", "gatsby",
        "electron", "react native", "flutter", "ionic",
    ],
    "ml_ai": [
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "pandas", "numpy", "matplotlib", "seaborn", "opencv",
        "hugging face", "huggingface", "transformers", "langchain",
        "machine learning", "deep learning", "nlp", "computer vision",
        "neural network", "cnn", "rnn", "lstm", "gan", "bert", "gpt",
        "reinforcement learning", "random forest", "svm", "xgboost",
        "gradient boosting", "decision tree", "clustering", "regression",
        "classification", "feature engineering", "model training",
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite",
        "oracle", "sql server", "cassandra", "dynamodb", "firebase",
        "supabase", "elasticsearch", "neo4j", "influxdb",
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "terraform", "ansible", "jenkins", "github actions", "gitlab ci",
        "ci/cd", "nginx", "apache", "vercel", "netlify", "heroku",
        "linux", "microservices", "serverless",
    ],
    "tools": [
        "git", "github", "gitlab", "jira", "figma", "postman",
        "swagger", "jupyter", "vscode", "webpack", "vite",
        "graphql", "rest api", "grpc", "kafka", "rabbitmq",
        "redis", "celery", "airflow",
    ],
}

# ─── Domain Keywords ─────────────────────────────────────
DOMAIN_KEYWORDS = {
    "Web Development": ["web", "frontend", "backend", "full stack", "fullstack", "website", "webapp", "web app"],
    "Machine Learning": ["machine learning", "ml", "deep learning", "neural", "model training", "prediction", "classification"],
    "Data Science": ["data science", "data analysis", "analytics", "visualization", "statistics", "data mining", "eda"],
    "AI/NLP": ["nlp", "natural language", "chatbot", "text processing", "sentiment", "llm", "transformer"],
    "Computer Vision": ["computer vision", "image processing", "object detection", "opencv", "cnn", "image recognition"],
    "Mobile Development": ["mobile", "android", "ios", "react native", "flutter", "app development"],
    "Cloud/DevOps": ["cloud", "devops", "deployment", "infrastructure", "ci/cd", "docker", "kubernetes"],
    "Database/Backend": ["database", "api", "backend", "server", "microservice", "rest", "graphql"],
}


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """
    Parse a resume from PDF bytes and extract structured information.
    
    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename for format detection.
        
    Returns:
        Dictionary with extracted resume data:
        - text: Full text content
        - skills: List of identified skills
        - experience: Experience description
        - education: Education description
        - domains: List of domain exposures
    """
    # Extract text based on file type
    if filename.lower().endswith(".pdf"):
        text = _extract_pdf_text(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")

    if not text.strip():
        return {
            "text": "",
            "skills": [],
            "experience": "Not specified",
            "education": "Not specified",
            "domains": [],
        }

    # Extract structured information
    skills = _extract_skills(text)
    experience = _extract_experience(text)
    education = _extract_education(text)
    domains = _extract_domains(text)

    return {
        "text": text,
        "skills": skills,
        "experience": experience,
        "education": education,
        "domains": domains,
    }


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    text_parts = []
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"PDF parsing error: {e}")
        return ""
    return "\n\n".join(text_parts)


def _extract_skills(text: str) -> list[str]:
    """Extract skills from resume text using keyword matching."""
    text_lower = text.lower()
    found_skills = set()

    for category, keywords in KNOWN_SKILLS.items():
        for skill in keywords:
            # Use word boundary matching for short skills
            if len(skill) <= 3:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.add(skill.title() if len(skill) > 2 else skill.upper())
            else:
                if skill in text_lower:
                    # Capitalize properly
                    found_skills.add(_capitalize_skill(skill))

    return sorted(list(found_skills))


def _capitalize_skill(skill: str) -> str:
    """Properly capitalize a skill name."""
    caps_map = {
        "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
        "java": "Java", "c++": "C++", "c#": "C#", "golang": "Go", "go": "Go",
        "rust": "Rust", "ruby": "Ruby", "php": "PHP", "swift": "Swift",
        "kotlin": "Kotlin", "scala": "Scala", "sql": "SQL",
        "react": "React", "angular": "Angular", "vue": "Vue.js",
        "svelte": "Svelte", "nextjs": "Next.js", "next.js": "Next.js",
        "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
        "express": "Express", "spring": "Spring", "spring boot": "Spring Boot",
        "tensorflow": "TensorFlow", "pytorch": "PyTorch", "keras": "Keras",
        "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
        "pandas": "Pandas", "numpy": "NumPy", "opencv": "OpenCV",
        "langchain": "LangChain", "huggingface": "HuggingFace",
        "docker": "Docker", "kubernetes": "Kubernetes",
        "aws": "AWS", "azure": "Azure", "gcp": "GCP",
        "mysql": "MySQL", "postgresql": "PostgreSQL", "mongodb": "MongoDB",
        "redis": "Redis", "sqlite": "SQLite", "firebase": "Firebase",
        "git": "Git", "github": "GitHub", "linux": "Linux",
        "machine learning": "Machine Learning", "deep learning": "Deep Learning",
        "nlp": "NLP", "computer vision": "Computer Vision",
        "neural network": "Neural Networks",
        "react native": "React Native", "flutter": "Flutter",
        "graphql": "GraphQL", "rest api": "REST API",
    }
    return caps_map.get(skill.lower(), skill.title())


def _extract_experience(text: str) -> str:
    """Extract experience information from resume text."""
    text_lower = text.lower()

    # Try to find years of experience patterns
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)',
        r'experience\s*[:\-]?\s*(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:in\s+)?(?:software|development|engineering|programming)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            years = match.group(1)
            return f"{years} years"

    # Check for experience section
    exp_section = _extract_section(text, ["experience", "work experience", "professional experience", "employment"])
    if exp_section:
        # Try to estimate from date ranges
        year_matches = re.findall(r'20\d{2}', exp_section)
        if year_matches:
            years_list = [int(y) for y in year_matches]
            span = max(years_list) - min(years_list)
            if span > 0:
                return f"~{span} years (estimated)"

    return "Not specified"


def _extract_education(text: str) -> str:
    """Extract education information from resume text."""
    edu_section = _extract_section(text, ["education", "academic", "qualification", "degree"])
    if edu_section:
        # Get first meaningful line
        lines = [l.strip() for l in edu_section.split('\n') if l.strip() and len(l.strip()) > 5]
        if lines:
            return " | ".join(lines[:3])  # First 3 lines of education

    # Try pattern matching
    degree_patterns = [
        r"(B\.?(?:Tech|Sc|E|A|S|Com)|M\.?(?:Tech|Sc|E|S|A|Com)|Ph\.?D|MBA|BCA|MCA)[.,\s]+([^\n,]+)",
        r"(Bachelor|Master|Doctor)\s+(?:of\s+)?([^\n,]+)",
    ]
    for pattern in degree_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()

    return "Not specified"


def _extract_domains(text: str) -> list[str]:
    """Identify domain exposure from resume text."""
    text_lower = text.lower()
    domains = []

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if domain not in domains:
                    domains.append(domain)
                break

    return domains


def _extract_section(text: str, section_headers: list[str]) -> str:
    """Extract a section of text based on common headers."""
    lines = text.split('\n')
    capturing = False
    section_lines = []

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()

        # Check if this line is a section header we're looking for
        if any(header in line_lower for header in section_headers):
            capturing = True
            continue

        # Check if we've hit the next section
        if capturing:
            # Common section headers that would end our capture
            end_headers = [
                "skills", "projects", "certifications", "achievements",
                "awards", "publications", "references", "interests",
                "languages", "experience", "education", "objective",
                "summary", "profile",
            ]
            if any(line_lower.startswith(h) or line_lower == h for h in end_headers):
                if line_lower not in [h for h in section_headers]:
                    break

            section_lines.append(line)

    return '\n'.join(section_lines).strip()
