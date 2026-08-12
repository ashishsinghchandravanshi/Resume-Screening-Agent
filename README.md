# Resume Screening Agent

Takes a **job description** and a **folder of resumes** (PDF/DOCX/TXT), and
produces a **ranked, scored shortlist with reasoning** for each candidate.

> **My agent takes** a job description + a folder of resumes, **and
> produces** a ranked CSV/JSON shortlist with a relevance score and
> plain-English reasoning per candidate.

---

## What it does

1. **Parses** resumes in PDF, DOCX, or TXT format into raw text.
2. **Extracts** structured data — skills, years of experience, and highest
   education — using an LLM (Groq / Llama 3.3 70B), with an automatic
   regex-based fallback if the API is unavailable.
3. **Scores** each resume against the job description using a blend of:
   - TF-IDF cosine similarity (overall semantic/textual fit)
   - Skill overlap with the JD's required skills
   - Experience-years match
   - Education-level match
4. **Ranks** all candidates and writes the result to `output/ranked_candidates.csv`
   and `output/ranked_candidates.json`, each with a human-readable reasoning
   string per candidate.

---

## Project structure

resume-screening-agent/
├── main.py # CLI entry point
├── pipeline.py # orchestrates parse -> extract -> score -> rank -> save
├── parse.py # PDF/DOCX/TXT text extraction
├── llm_extraction.py # Groq LLM call for skills/experience/education
├── structure_extraction.py # regex-based extraction (fallback + JD skill parsing)
├── scoring.py # TF-IDF similarity + weighted scoring formula
├── job_description.txt # sample JD
├── resumes/ # sample resumes
├── output/ # generated ranked_candidates.csv / .json
├── requirements.txt
└── SCORING_METHOD.md # deep-dive on the scoring formula
---

## Setup

### 1. Clone and install dependencies
```bash
git clone https://github.com/ashishsinghchandravanshi/Resume-Screening-Agent.git
cd Resume-Screening-Agent
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Get a free Groq API key
- Sign up at [console.groq.com](https://console.groq.com)
- Create an API key
- Create a file named `.env` in the project root with:

### 3. Run it
```bash
python main.py
```
This uses the default paths (`job_description.txt`, `resumes/`, `output/`).
You can also specify custom paths:
```bash
python main.py --jd job_description.txt --resumes resumes --out output
```

If you don't have an API key handy, run in regex-only mode (no LLM call, still fully functional):
```bash
python main.py --no-llm
```

### Output
Ranked 13 candidates against JD.

Rank Candidate Score Yrs Education

1 Neha Kapoor 56.89 9.0 Master's (M.Tech)
2 Ananya Sharma 56.05 7.0 Bachelor's (B.Tech)
...
Saved: output/ranked_candidates.json
Saved: output/ranked_candidates.csv
---

## Design choices

**Why Groq (Llama 3.3 70B) for extraction?**
Regex/keyword matching only catches skills it's explicitly told about, and
misses synonyms ("K8s" vs "Kubernetes", "Postgres" vs "PostgreSQL") or
context-dependent experience statements. An LLM reads the resume the way a
recruiter would. Groq was chosen because it's free-tier friendly and very
fast — important when processing many resumes per run.

**Why keep a regex fallback?**
LLM calls can fail (network issue, rate limit, missing key). Rather than
crashing the whole batch, `llm_extraction.py` catches any failure and
transparently falls back to the original regex extractor per-resume, so
the agent degrades gracefully instead of breaking.

**Why TF-IDF (not embeddings) for overall similarity?**
It's zero-cost, deterministic, and fast — no extra API calls needed for the
semantic-fit component, while the more error-prone skill/experience/education
extraction is handled by the LLM.

**Why a weighted blend instead of one score?**
- Text similarity (45%) — most holistic signal.
- Skill match (35%) — concrete tool/tech overlap predicts productivity.
- Experience (15%) and education (5%) — weighted lower, computed as
  *capped ratios* not hard cutoffs, so a candidate just under the
  experience bar isn't zeroed out.

Full formula: see [`SCORING_METHOD.md`](SCORING_METHOD.md).

---

## Sample inputs/outputs

- Job description: [`job_description.txt`](job_description.txt) — Senior
  Backend Software Engineer role.
- Sample resumes: [`resumes/`](resumes) — mix of strong/weak fits to show
  the ranking actually differentiates candidates.
- Sample output: [`output/ranked_candidates.csv`](output/ranked_candidates.csv)
  and [`output/ranked_candidates.json`](output/ranked_candidates.json)

---

## Tradeoffs & what I'd improve with more time

- **LLM extraction is sequential**, one resume at a time. At scale this
  should be batched/parallelized with async calls.
- **No caching** — re-running the same resumes re-calls the LLM every time.
  A hash-based local cache would make re-runs free and instant.
- **TF-IDF is bag-of-words** — it can't tell "K8s" and "Kubernetes" are
  related in the similarity score (though the LLM extraction step already
  normalizes this for the skill-match component). Swapping in sentence
  embeddings would improve the semantic layer further.
- **PDF parsing is text-layer only** — scanned/image PDFs would need OCR,
  which isn't implemented yet.
- This is a **screening aid**, not an auto-reject tool — scores are meant
  to narrow a shortlist for human review.

---

## Every file, in one line each

- `parse.py` — reads text out of `.pdf`/`.docx`/`.txt` based on extension.
- `structure_extraction.py` — regex-based skill/experience/education extractor (fallback + JD parsing).
- `llm_extraction.py` — calls Groq to extract skills/experience/education; falls back to regex on failure.
- `scoring.py` — TF-IDF similarity + weighted scoring formula + reasoning text.
- `pipeline.py` — orchestrates parse → extract → score → rank → save.
- `main.py` — CLI entry point.