"""
llm_extraction.py
==================
Uses Groq's LLM API (Llama 3.3 70B) to extract structured data — skills,
experience years, and education — from raw resume text. This replaces
pure regex/keyword matching with an LLM that can understand context,
synonyms, and phrasing regex would miss (e.g. "K8s" == "Kubernetes",
"5+ yrs in backend dev" == 5 years experience).

Falls back to the regex-based extractor (structure_extraction.py) if the
API call fails, so the agent never crashes due to a network/API issue.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load .env explicitly here too, so the Groq client always has the key
# regardless of import order (this module can get imported before
# main.py's own load_dotenv() call runs).
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from structure_extraction import (
    extract_skills as regex_extract_skills,
    extract_experience_years as regex_extract_experience_years,
    extract_education as regex_extract_education,
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a resume-parsing assistant. Given raw resume text,
extract structured information and return ONLY a valid JSON object — no
markdown, no explanation, no code fences. The JSON must have exactly this
shape:

{
  "skills": ["Python", "AWS", "Docker", ...],
  "experience_years": 5.0,
  "education_label": "Bachelor's (B.Tech)",
  "education_rank": 3
}

Rules:
- "skills": list every technical skill, tool, framework, language, or
  platform mentioned (normalize variants, e.g. "K8s" -> "Kubernetes",
  "JS" -> "JavaScript", "Postgres" -> "PostgreSQL").
- "experience_years": total years of professional experience as a number
  (use the candidate's own stated total if given, otherwise estimate from
  role durations). Use 0 if none is discernible.
- "education_label": the highest degree found, formatted like one of:
  "PhD", "Master's (M.Tech)", "Master's (M.S.)", "MBA",
  "Bachelor's (B.Tech)", "Bachelor's (B.E.)", "Bachelor's (B.S.)",
  "Bachelor's (BCA)", or "Not specified" if none found.
- "education_rank": PhD=5, Master's/MBA=4, Bachelor's=3, BCA=2, none=0.
"""


def llm_extract(text: str) -> dict:
    """
    Call Groq to extract skills/experience/education from resume text.
    Returns a dict: {skills, experience_years, education_label, education_rank}
    Falls back to regex extraction on any failure (missing key, API error,
    malformed JSON, etc.) so the pipeline is never blocked by the LLM call.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text[:6000]},  # keep prompt small/cheap
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)

        # Basic validation — if the model returns a malformed shape, fall back
        if not isinstance(data.get("skills"), list):
            raise ValueError("Malformed 'skills' field from LLM")

        return {
            "skills": data.get("skills", []),
            "experience_years": float(data.get("experience_years", 0) or 0),
            "education_label": data.get("education_label", "Not specified"),
            "education_rank": int(data.get("education_rank", 0) or 0),
        }

    except Exception as e:
        print(f"[llm_extraction] Falling back to regex extraction ({e})")
        return {
            "skills": regex_extract_skills(text),
            "experience_years": regex_extract_experience_years(text),
            "education_label": regex_extract_education(text)[0],
            "education_rank": regex_extract_education(text)[1],
        }