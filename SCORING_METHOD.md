\# Resume Screening Agent — Scoring Method



\## Pipeline overview



1\. \*\*Parse\*\* — Each resume (`.pdf`, `.docx`, or `.txt`) is converted to plain

&#x20;  text: `pypdf` for PDFs, `python-docx` for Word files, direct read for text

&#x20;  files.

2\. \*\*Extract\*\* — From the raw text, the agent pulls three structured

&#x20;  signals via an LLM call (Groq, Llama 3.3 70B) with a strict JSON-output

&#x20;  prompt:

&#x20;  - \*\*Skills\*\* — the model reads the resume the way a recruiter would and

&#x20;    normalizes synonyms (e.g. "K8s" -> "Kubernetes", "Postgres" ->

&#x20;    "PostgreSQL") that a fixed regex vocabulary would miss.

&#x20;  - \*\*Experience (years)\*\* — the model reads the candidate's stated total

&#x20;    or estimates from role durations/date ranges, handling phrasing regex

&#x20;    can't (e.g. "led the last 3 of my 6 years as a manager" -> 6 years).

&#x20;  - \*\*Education\*\* — the model returns the highest degree found, mapped to

&#x20;    a 0-5 rank for numeric comparison.



&#x20;  If the LLM call fails for any reason (no API key, network issue, rate

&#x20;  limit, malformed response), the agent automatically falls back to a

&#x20;  regex-based extractor (`structure\_extraction.py`) for that resume, so a

&#x20;  single failed call never blocks the whole run. The JD's own required-skill

&#x20;  list is always computed via the regex extractor -- this keeps the

&#x20;  "ground truth" being scored against deterministic and free to compute.



3\. \*\*Score\*\* — Four signals are combined into one 0-100 score per candidate

&#x20;  (see weights below).

4\. \*\*Rank \& explain\*\* — Candidates are sorted by final score, and a

&#x20;  plain-English reasoning string is generated per candidate (score

&#x20;  breakdown, matched/missing skills, experience and education gaps).

5\. \*\*Output\*\* — Results are written to `ranked\_candidates.csv` and

&#x20;  `ranked\_candidates.json`.



\## Scoring formula



final\_score = 100 x ( 0.45 x text\_similarity

\+ 0.35 x skill\_match

\+ 0.15 x experience\_score

\+ 0.05 x education\_score )



| Component | Weight | How it's computed |

|---|---|---|

| \*\*Text similarity\*\* | 45% | TF-IDF vectorization of the JD and every resume, then cosine similarity between the JD vector and each resume vector. Captures overall semantic/contextual fit beyond just a skills checklist. |

| \*\*Skill match\*\* | 35% | `(skills in resume matched with skills in JD) / (skills in JD)`. The JD's own text is run through the same regex skill extractor, so the "required skill set" is derived from the JD rather than hardcoded. |

| \*\*Experience score\*\* | 15% | `min(candidate\_years / required\_years, 1.0)`. Capped at 1.0 so 15 years of experience doesn't drown out other signals. |

| \*\*Education score\*\* | 5% | `min(candidate\_degree\_rank / required\_degree\_rank, 1.0)`. Weighted lowest because education is typically a gate/filter rather than a differentiator once the minimum is met. |



\### Why these weights

\- \*\*Text similarity is weighted highest\*\* because it's the most holistic

&#x20; signal -- it rewards resumes whose overall narrative matches the role.

\- \*\*Skill match is weighted second\*\* because for a technical role, concrete

&#x20; tool/technology overlap is highly predictive of a candidate's ability to

&#x20; be productive quickly.

\- \*\*Experience and education are weighted lower\*\* and both use a \*capped

&#x20; ratio\* (not a hard cutoff) -- someone with 4.5 years isn't zeroed out for

&#x20; falling under a "5+ years" line, they're scored proportionally.



\## Why an LLM (Groq / Llama 3.3 70B) instead of pure regex?



Regex/keyword matching only catches skills it's explicitly told about, and

misses synonyms or context-dependent phrasing. An LLM reads the resume more

like a human recruiter would -- normalizing variants, understanding phrases

like "5+ yrs in backend roles," and generalizing to skills that were never

hardcoded into a vocabulary list. Groq was chosen specifically because it

offers a generous free tier and very low latency, which matters when

processing many resumes in a single run.



\## Known limitations



\- The LLM extraction step is called once per resume, sequentially -- at

&#x20; larger scale (100s of resumes) this should be parallelized with async

&#x20; calls to reduce total run time.

\- No caching layer exists yet -- re-running the same resume set re-calls

&#x20; the LLM every time. A hash-based local cache (skip re-extraction if a

&#x20; resume's text hasn't changed) would make repeat runs instant and free.

\- TF-IDF similarity is bag-of-words -- it doesn't understand synonyms the

&#x20; way an embedding-based model would. This is partially mitigated by the

&#x20; LLM already normalizing skill terms during extraction, but the overall

&#x20; text-similarity score itself doesn't benefit from that normalization.

&#x20; Swapping in sentence embeddings would improve semantic matching further.

\- Experience-year extraction depends on the resume text being reasonably

&#x20; well-structured; extremely unconventional formats could still confuse

&#x20; even the LLM step.

\- PDF parsing is text-layer only -- scanned/image-based PDFs are not

&#x20; supported without adding OCR (e.g. `pytesseract`).

\- This is a screening aid, not a hiring decision-maker -- scores should

&#x20; narrow a shortlist for human review, not auto-reject candidates.

