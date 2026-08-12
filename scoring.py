from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

WEIGHT_TEXT_SIMILARITY = 0.45   # overall semantic/textual fit (TF-IDF cosine)
WEIGHT_SKILL_MATCH = 0.35       # required-skill coverage
WEIGHT_EXPERIENCE = 0.15        # years of experience vs JD requirement
WEIGHT_EDUCATION = 0.05         # degree level vs JD requirement

REQUIRED_MIN_YEARS = 5          # pulled from the JD's "5+ years" requirement
REQUIRED_MIN_DEGREE_RANK = 3    # Bachelor's


def compute_text_similarity(jd_text: str, resume_texts: list) -> list:
    """TF-IDF + cosine similarity between the JD and each resume."""
    corpus = [jd_text] + resume_texts
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(corpus)
    sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
    return sims.tolist()


def score_candidate(jd_skills: set, candidate: dict, text_sim: float) -> dict:
    cand_skills = set(candidate["skills"])
    matched = jd_skills & cand_skills
    missing = jd_skills - cand_skills
    skill_score = len(matched) / len(jd_skills) if jd_skills else 0.0

    years = candidate["experience_years"]
    experience_score = min(years / REQUIRED_MIN_YEARS, 1.0) if REQUIRED_MIN_YEARS else 1.0

    degree_rank = candidate["education_rank"]
    education_score = min(degree_rank / REQUIRED_MIN_DEGREE_RANK, 1.0) if REQUIRED_MIN_DEGREE_RANK else 1.0

    final = (
        WEIGHT_TEXT_SIMILARITY * text_sim
        + WEIGHT_SKILL_MATCH * skill_score
        + WEIGHT_EXPERIENCE * experience_score
        + WEIGHT_EDUCATION * education_score
    ) * 100

    return {
        "final_score": round(final, 2),
        "text_similarity_pct": round(text_sim * 100, 1),
        "skill_match_pct": round(skill_score * 100, 1),
        "experience_score_pct": round(experience_score * 100, 1),
        "education_score_pct": round(education_score * 100, 1),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
    }


def build_reasoning(name: str, candidate: dict, scores: dict) -> str:
    matched = scores["matched_skills"]
    missing = scores["missing_skills"]
    years = candidate["experience_years"]
    degree = candidate["education_label"]

    parts = [
        f"Score {scores['final_score']}/100.",
        f"{years} yrs experience (JD requires {REQUIRED_MIN_YEARS}+); education: {degree}.",
        f"Matched {len(matched)}/{len(matched) + len(missing)} required skills"
        + (f" ({', '.join(matched[:6])}{'...' if len(matched) > 6 else ''})" if matched else ""),
    ]
    if missing:
        parts.append(f"Missing: {', '.join(missing[:6])}{'...' if len(missing) > 6 else ''}.")
    if years < REQUIRED_MIN_YEARS:
        parts.append("Below the minimum experience bar.")
    if candidate["education_rank"] < REQUIRED_MIN_DEGREE_RANK:
        parts.append("Below the minimum education requirement.")
    return " ".join(parts)