import os
import json
import csv
from pathlib import Path

from parse import extract_text
from structure_extraction import extract_skills as regex_extract_skills
from llm_extraction import llm_extract
from scoring import compute_text_similarity, score_candidate, build_reasoning


def run_pipeline(jd_path: str, resumes_dir: str, out_dir: str, use_llm: bool = True):
    jd_text = extract_text(jd_path)

    # The JD's required skill set: we use the regex extractor here (not the
    # LLM) so the "required skills" list stays fast, deterministic, and free
    # to compute — it's a fixed reference document, not a resume.
    jd_skills = set(regex_extract_skills(jd_text))

    resume_files = sorted(
        f for f in os.listdir(resumes_dir)
        if Path(f).suffix.lower() in {".txt", ".docx", ".pdf"}
    )
    if len(resume_files) < 1:
        raise SystemExit(f"No resumes found in {resumes_dir}")

    candidates = []
    raw_texts = []
    for fname in resume_files:
        fpath = os.path.join(resumes_dir, fname)
        text = extract_text(fpath)
        raw_texts.append(text)
        name = Path(fname).stem.replace("_", " ")

        if use_llm:
            print(f"[pipeline] Extracting via LLM: {fname}")
            extracted = llm_extract(text)
        else:
            from structure_extraction import extract_experience_years, extract_education
            edu_label, edu_rank = extract_education(text)
            extracted = {
                "skills": regex_extract_skills(text),
                "experience_years": extract_experience_years(text),
                "education_label": edu_label,
                "education_rank": edu_rank,
            }

        candidates.append({
            "file": fname,
            "name": name,
            "skills": extracted["skills"],
            "experience_years": extracted["experience_years"],
            "education_label": extracted["education_label"],
            "education_rank": extracted["education_rank"],
        })

    text_sims = compute_text_similarity(jd_text, raw_texts)

    results = []
    for candidate, sim in zip(candidates, text_sims):
        scores = score_candidate(jd_skills, candidate, sim)
        reasoning = build_reasoning(candidate["name"], candidate, scores)
        results.append({
            "candidate": candidate["name"],
            "file": candidate["file"],
            "final_score": scores["final_score"],
            "experience_years": candidate["experience_years"],
            "education": candidate["education_label"],
            "text_similarity_pct": scores["text_similarity_pct"],
            "skill_match_pct": scores["skill_match_pct"],
            "matched_skills": scores["matched_skills"],
            "missing_skills": scores["missing_skills"],
            "reasoning": reasoning,
        })

    results.sort(key=lambda r: r["final_score"], reverse=True)
    for i, r in enumerate(results, start=1):
        r["rank"] = i

    os.makedirs(out_dir, exist_ok=True)

    # JSON output
    json_path = os.path.join(out_dir, "ranked_candidates.json")
    with open(json_path, "w") as f:
        json.dump({
            "job_description_file": os.path.basename(jd_path),
            "required_skills_detected_in_jd": sorted(jd_skills),
            "extraction_method": "llm" if use_llm else "regex",
            "num_candidates": len(results),
            "ranking": results,
        }, f, indent=2)

    # CSV output
    csv_path = os.path.join(out_dir, "ranked_candidates.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "Candidate", "File", "Final Score", "Experience (yrs)",
            "Education", "Text Similarity %", "Skill Match %",
            "Matched Skills", "Missing Skills", "Reasoning"
        ])
        for r in results:
            writer.writerow([
                r["rank"], r["candidate"], r["file"], r["final_score"],
                r["experience_years"], r["education"], r["text_similarity_pct"],
                r["skill_match_pct"], "; ".join(r["matched_skills"]),
                "; ".join(r["missing_skills"]), r["reasoning"],
            ])

    return results, json_path, csv_path
