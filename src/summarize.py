"""
Ranks and summarizes candidate SAM.gov opportunities with OpenAI in a single
chat completion call (cheap on purpose -- see DEFAULT_OPENAI_MODEL in
config.py). Produces the top N job-related picks plus one "for funzies" pick,
each with a short TLDR blurb.
"""

from __future__ import annotations

import json
import os

from openai import OpenAI

from config import (
    DEFAULT_OPENAI_MODEL,
    NUM_FUN_RECOMMENDATIONS,
    NUM_JOB_RECOMMENDATIONS,
    PROFILE_BLURB,
)

MAX_DESCRIPTION_CHARS = 600  # trim per-opportunity text sent to the model
MAX_CANDIDATES_PER_POOL = 40  # cap tokens if a query returns a huge pool

SYSTEM_PROMPT = """You help a defense-contracting engineer triage new SAM.gov \
contract opportunities. You will be given a profile describing their job and \
hobbies, a list of "job" candidate opportunities, and a list of "hobby" \
candidate opportunities pulled from SAM.gov.

Pick the {num_job} job opportunities most relevant to the profile's job \
description, ranked best-first. Then pick exactly {num_fun} opportunity from \
the hobby candidates that seems like the most fun or interesting oddball \
find -- it doesn't need to be a perfect match, just something amusing or \
neat someone with a truck and hobby-electrical/software interests might \
enjoy reading about.

For every pick, write a 1-2 sentence plain-English TLDR of what the work is, \
plus a short "why_relevant" note tying it to the profile.

Respond with ONLY a JSON object matching this exact shape, no markdown \
fences, no commentary:
{{
  "overall_tldr": "2-3 sentence summary of today's batch overall",
  "job_recommendations": [
    {{"notice_id": "...", "title": "...", "agency": "...", "naics": "...",
      "set_aside": "...", "posted_date": "...", "response_deadline": "...",
      "link": "...", "tldr": "...", "why_relevant": "..."}}
  ],
  "fun_recommendation": {{"notice_id": "...", "title": "...", "agency": "...",
      "naics": "...", "set_aside": "...", "posted_date": "...",
      "response_deadline": "...", "link": "...", "tldr": "...",
      "why_relevant": "..."}}
}}

If there are fewer than {num_job} job candidates, return as many as are \
available. If there are no hobby candidates at all, omit fun_recommendation."""


def _compact(opp: dict) -> dict:
    """Trim a raw SAM.gov opportunity dict down to what the model needs."""
    return {
        "notice_id": opp.get("noticeId", ""),
        "title": opp.get("title", ""),
        "agency": opp.get("fullParentPathName") or opp.get("department", ""),
        "naics": opp.get("naicsCode", ""),
        "set_aside": opp.get("typeOfSetAsideDescription", ""),
        "posted_date": opp.get("postedDate", ""),
        "response_deadline": opp.get("responseDeadLine", ""),
        "link": opp.get("uiLink", ""),
        "description_snippet": (opp.get("description_text", "") or "")[:MAX_DESCRIPTION_CHARS],
    }


def rank_and_summarize(job_pool: list[dict], hobby_pool: list[dict]) -> dict:
    """
    Calls OpenAI once with the two candidate pools and returns the parsed
    JSON result described in SYSTEM_PROMPT. Raises RuntimeError on API
    failure or unparsable output -- callers should catch and fall back to a
    "no picks today" page rather than crash the whole pipeline.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    client = OpenAI(api_key=api_key)

    job_candidates = [_compact(o) for o in job_pool[:MAX_CANDIDATES_PER_POOL]]
    hobby_candidates = [_compact(o) for o in hobby_pool[:MAX_CANDIDATES_PER_POOL]]

    user_content = json.dumps(
        {
            "profile": PROFILE_BLURB,
            "job_candidates": job_candidates,
            "hobby_candidates": hobby_candidates,
        }
    )

    system_prompt = SYSTEM_PROMPT.format(
        num_job=NUM_JOB_RECOMMENDATIONS, num_fun=NUM_FUN_RECOMMENDATIONS
    )

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse OpenAI response as JSON: {exc}\nRaw: {raw[:500]}")
