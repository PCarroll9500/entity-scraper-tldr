"""
Orchestrates one end-to-end run:
  1. Pull job-pool and hobby-pool candidate opportunities from SAM.gov
  2. Fetch full descriptions for a manageable subset of each pool
  3. Rank + summarize with OpenAI into 9 job picks + 1 fun pick
  4. Render docs/index.html (GitHub Pages) and stash raw data for debugging

Run with: python src/main.py
Requires env vars SAM_API_KEY and OPENAI_API_KEY (see .env.example).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv

    load_dotenv()  # no-op if .env doesn't exist; CI sets real env vars directly
except ImportError:
    pass

from config import (
    HOBBY_KEYWORDS,
    HOBBY_NAICS_CODES,
    JOB_KEYWORDS,
    JOB_NAICS_CODES,
    LOOKBACK_DAYS,
    MAX_RESULTS_PER_QUERY,
)
from sam_client import collect_pool, fetch_description
from summarize import rank_and_summarize
from build_page import write_page

# How many opportunities per pool get a full-description fetch. Keep small --
# each is an extra HTTP call and most candidates won't make the final cut.
DESCRIPTION_FETCH_LIMIT = 25


def _date_window() -> tuple[str, str]:
    today = datetime.utcnow().date()
    start = today - timedelta(days=LOOKBACK_DAYS)
    fmt = "%m/%d/%Y"
    return start.strftime(fmt), today.strftime(fmt)


def _hydrate_descriptions(api_key: str, pool: list[dict], limit: int) -> None:
    """Mutates each opportunity dict in-place, adding 'description_text'."""
    for opp in pool[:limit]:
        opp["description_text"] = fetch_description(api_key, opp.get("description", ""))


def main() -> int:
    sam_api_key = os.environ.get("SAM_API_KEY")
    if not sam_api_key:
        print("ERROR: SAM_API_KEY is not set. Get a free key from your SAM.gov "
              "account profile and set it as an env var / repo secret.", file=sys.stderr)
        return 1

    posted_from, posted_to = _date_window()
    print(f"Searching SAM.gov opportunities posted {posted_from} - {posted_to}")

    job_pool = collect_pool(
        sam_api_key, posted_from, posted_to, JOB_NAICS_CODES, JOB_KEYWORDS,
        limit_per_query=MAX_RESULTS_PER_QUERY,
    )
    hobby_pool = collect_pool(
        sam_api_key, posted_from, posted_to, HOBBY_NAICS_CODES, HOBBY_KEYWORDS,
        limit_per_query=MAX_RESULTS_PER_QUERY,
    )
    print(f"Job pool: {len(job_pool)} candidates | Hobby pool: {len(hobby_pool)} candidates")

    _hydrate_descriptions(sam_api_key, job_pool, DESCRIPTION_FETCH_LIMIT)
    _hydrate_descriptions(sam_api_key, hobby_pool, DESCRIPTION_FETCH_LIMIT)

    os.makedirs("data", exist_ok=True)
    with open("data/latest_raw.json", "w", encoding="utf-8") as f:
        json.dump({"job_pool": job_pool, "hobby_pool": hobby_pool}, f, indent=2)

    try:
        result = rank_and_summarize(job_pool, hobby_pool)
    except RuntimeError as exc:
        print(f"ERROR: summarization failed: {exc}", file=sys.stderr)
        result = {
            "overall_tldr": (
                "Summarization failed this run -- see data/latest_raw.json for "
                "the raw candidates that were pulled."
            ),
            "job_recommendations": [],
            "fun_recommendation": None,
        }

    with open("data/latest_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    os.makedirs("docs", exist_ok=True)
    write_page(result)
    print("Wrote docs/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
