import argparse
from dotenv import load_dotenv
from pipeline import run_pipeline

from pathlib import Path
load_dotenv()
 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resume Screening Agent")
    parser.add_argument("--jd", default="job_description.txt")
    parser.add_argument("--resumes", default="resumes")
    parser.add_argument("--out", default="output")
    parser.add_argument(
        "--no-llm", action="store_true",
        help="Skip the Groq LLM call and use regex-only extraction instead."
    )
    args = parser.parse_args()

    results, json_path, csv_path = run_pipeline(
        args.jd, args.resumes, args.out, use_llm=not args.no_llm
    )

    print(f"\nRanked {len(results)} candidates against JD.\n")
    print(f"{'Rank':<5}{'Candidate':<20}{'Score':<8}{'Yrs':<6}{'Education'}")
    print("-" * 70)
    for r in results:
        print(f"{r['rank']:<5}{r['candidate']:<20}{r['final_score']:<8}{r['experience_years']:<6}{r['education']}")
    print(f"\nSaved: {json_path}\nSaved: {csv_path}")
