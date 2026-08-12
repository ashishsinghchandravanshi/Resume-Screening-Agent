import re

SKILL_VOCAB = [
    "Python", "Java", "JavaScript", "TypeScript", "Node.js", "React",
    "Django", "Flask", "FastAPI", "Django REST Framework", "Spring Boot",
    "REST API", "Microservices", "GraphQL",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "DynamoDB",
    "AWS", "Azure", "GCP", "Terraform", "Docker", "Kubernetes",
    "CI/CD", "Jenkins", "GitHub Actions", "GitLab CI",
    "Kafka", "RabbitMQ", "Git", "Agile", "Scrum",
    "Prometheus", "Grafana", "ELK", "System Design", "Mentoring",
    "Pandas", "Tableau", "Excel", "Selenium", "PyTest",
]

EDUCATION_PATTERNS = [
    (r"\bph\.?d\b", "PhD"),
    (r"\bm\.?tech\b|\bmaster of technology\b", "Master's (M.Tech)"),
    (r"\bm\.?s\.?\b|\bmaster of science\b", "Master's (M.S.)"),
    (r"\bmba\b", "MBA"),
    (r"\bb\.?tech\b|\bbachelor of technology\b", "Bachelor's (B.Tech)"),
    (r"\bb\.?e\.?\b|\bbachelor of engineering\b", "Bachelor's (B.E.)"),
    (r"\bb\.?s\.?\b|\bbachelor of science\b", "Bachelor's (B.S.)"),
    (r"\bbca\b|\bbachelor of computer applications\b", "Bachelor's (BCA)"),
]

# Highest degree first = better rank
DEGREE_RANK = {
    "PhD": 5,
    "Master's (M.Tech)": 4,
    "Master's (M.S.)": 4,
    "MBA": 4,
    "Bachelor's (B.Tech)": 3,
    "Bachelor's (B.E.)": 3,
    "Bachelor's (B.S.)": 3,
    "Bachelor's (BCA)": 2,
}


def extract_skills(text: str) -> list:
    """Return the subset of SKILL_VOCAB found in the resume text."""
    found = []
    text_lower = text.lower()
    for skill in SKILL_VOCAB:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def extract_experience_years(text: str) -> float:
    """
    Estimate total years of professional experience.
    Strategy: look for an explicit summary figure like "7 years of experience"
    first; fall back to summing per-role "(N years)" annotations.
    """
    summary_matches = re.findall(
        r"(\d+(?:\.\d+)?)\+?\s*years?\s+(?:of\s+)?(?:professional\s+)?experience",
        text, re.IGNORECASE
    )
    if summary_matches:
        return max(float(m) for m in summary_matches)

    role_matches = re.findall(r"\((\d+(?:\.\d+)?)\s*years?\)", text, re.IGNORECASE)
    if role_matches:
        return round(sum(float(m) for m in role_matches), 1)

    return 0.0


def extract_education(text: str) -> tuple:
    """Return (highest_degree_label, rank_score 0-5) found in the resume."""
    best_label, best_rank = "Not specified", 0
    text_lower = text.lower()
    for pattern, label in EDUCATION_PATTERNS:
        if re.search(pattern, text_lower):
            rank = DEGREE_RANK[label]
            if rank > best_rank:
                best_rank, best_label = rank, label
    return best_label, best_rank