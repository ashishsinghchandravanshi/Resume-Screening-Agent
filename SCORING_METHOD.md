# Resume Screening Agent — Scoring Method

## Pipeline overview

1. **Parse** — Each resume (`.pdf`, `.docx`, or `.txt`) is converted to plain text: `pypdf` for PDFs, `python-docx` for Word files, direct read for text files.
2. **Extract** — From the raw text, the agent pulls three structured signals via an LLM call (Groq, Llama 3.3 70B) with a strict JSON-output prompt:
   - **Skills** — the model reads the resume the way a recruiter would and normalizes synonyms (e.g. "K8s" -> "Kubernetes", "Postgres" -> "PostgreSQL") that a fixed regex vocabulary would miss.
   - **Experience (years)** — the model reads the candidate's stated total or estimates from role durations/date ranges, handling phrasing regex can't (e.g. "led the last 3 of my 6 years as a manager" -> 6 years).
   - **Education** — the model returns the highest degree found, mapped to a 0-5 rank for numeric comparison.

   If the LLM call fails for any reason (no API key, network issue, rate limit, malformed response), the agent automatically falls back to a regex-based extractor (`structure_extraction.py`) for that resume, so a single failed call never blocks the whole run. The JD's own required-skill list is always computed via the regex extractor -- this keeps the "ground truth" being scored against deterministic and free to compute.

3. **Score** — Four signals are combined into one 0-100 score per candidate (see weights below).
4. **Rank & explain** — Candidates are sorted by final score, and a plain-English reasoning string is generated per candidate (score breakdown, matched/missing skills, experience and education gaps).
5. **Output** — Results are written to `ranked_candidates.csv` and `ranked_candidates.json`.

## Scoring formula

final_score = 100 x ( 0.45 x text_similarity
                     + 0.35 x skill_match
                     + 0.15 x experience_score
                     + 0.05 x education_score )

| Component | Weight | How it's computed |
|---|---|---|
| **Text similarity** | 45% | TF-IDF vectorization of the JD and every resume, then cosine similarity between the JD vector and each resume vector. Captures overall semantic/contextual fit beyond just a skills checklist. |
| **Skill match** | 35% | `(skills in resume matched with skills in JD) / (skills in JD)`. The JD's own text is run through the same regex skill extractor, so the "required skill set" is derived from the JD rather than hardcoded. |
| **Experience score** | 15% | `min(candidate_years / required_years, 1.0)`. Capped at 1.0 so 15 years of experience doesn't drown out other signals. |
| **Education score** | 5% | `min(candidate_degree_rank / required_degree_rank, 1.0)`. Weighted lowest because education is typically a gate/filter rather than a differentiator once the minimum is met. |

### Why these weights
- **Text similarity is weighted highest** because it's the most holistic signal -- it rewards resumes whose overall narrative matches the role.
- **Skill match is weighted second** because for a technical role, concrete tool/technology overlap is highly predictive of a candidate's ability to be productive quickly.
- **Experience and education are weighted lower** and both use a *capped ratio* (not a hard cutoff) -- someone with 4.5 years isn't zeroed out for falling under a "5+ years" line, they're scored proportionally.

## Why an LLM (Groq / Llama 3.3 70B) instead of pure regex?

Regex/keyword matching only catches skills it's explicitly told about, and misses synonyms or context-dependent phrasing. An LLM reads the resume more like a human recruiter would -- normalizing variants, understanding phrases like "5+ yrs in backend roles," and generalizing to skills that were never hardcoded into a vocabulary list. Groq was chosen specifically because it offers a generous free tier and very low latency, which matters when processing many resumes in a single run.

## Known limitations

- The LLM extraction step is called once per resume, sequentially -- at larger scale (100s of resumes) this should be parallelized with async calls to reduce total run time.
- No caching layer exists yet -- re-running the same resume set re-calls the LLM every time. A hash-based local cache (skip re-extraction if a resume's text hasn't changed) would make repeat runs instant and free.
- TF-IDF similarity is bag-of-words -- it doesn't understand synonyms the way an embedding-based model would. This is partially mitigated by the LLM already normalizing skill terms during extraction, but the overall text-similarity score itself doesn't benefit from that normalization. Swapping in sentence embeddings would improve semantic matching further.
- Experience-year extraction depends on the resume text being reasonably well-structured; extremely unconventional formats could still confuse even the LLM step.
- PDF parsing is text-layer only -- scanned/image-based PDFs are not supported without adding OCR (e.g. `pytesseract`).
- This is a screening aid, not a hiring decision-maker -- scores should narrow a shortlist for human review, not auto-reject candidates.