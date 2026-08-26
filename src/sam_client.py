"""
Thin wrapper around the SAM.gov "Get Opportunities" public API (v2).

Docs: https://open.gsa.gov/api/get-opportunities-public-api/
Requires a free SAM.gov API key -- request one from your SAM.gov account
profile page and set it as the SAM_API_KEY environment variable / repo
secret. This module never scrapes the SAM.gov website directly; it only
calls the official public API.
"""

from __future__ import annotations

import time
from typing import Iterable

import requests

BASE_URL = "https://api.sam.gov/opportunities/v2/search"
DESCRIPTION_TIMEOUT = 15
SEARCH_TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5
INTER_QUERY_DELAY_SECONDS = 2  # pace back-to-back search calls to avoid 429s


def _get_with_retry(url: str, params: dict, timeout: int) -> requests.Response:
    last_exc = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 429:
                # rate limited -- back off and retry
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"SAM.gov request failed after {RETRY_ATTEMPTS} attempts: {last_exc}")


def search_opportunities(
    api_key: str,
    posted_from: str,
    posted_to: str,
    naics: str | None = None,
    title_keyword: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """
    One search call against the v2 opportunities endpoint. postedFrom/postedTo
    must be MM/dd/yyyy strings. Returns the raw opportunitiesData list (empty
    list on a well-formed empty response).
    """
    params = {
        "api_key": api_key,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": limit,
        "offset": offset,
    }
    if naics:
        params["ncode"] = naics
    if title_keyword:
        params["title"] = title_keyword

    resp = _get_with_retry(BASE_URL, params, SEARCH_TIMEOUT)
    payload = resp.json()
    return payload.get("opportunitiesData", []) or []


def fetch_description(api_key: str, description_url: str) -> str:
    """
    The v2 search response's `description` field is a URL to a separate
    endpoint that returns the full notice text, not the text itself. Fetch
    it, tolerating failures (some notices 404 or are archived).
    """
    if not description_url:
        return ""
    try:
        resp = requests.get(
            description_url,
            params={"api_key": api_key},
            timeout=DESCRIPTION_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        # The endpoint typically returns {"description": "<html or text>"}
        if isinstance(data, dict):
            return data.get("description", "") or ""
        return str(data)
    except Exception:
        return ""


def collect_pool(
    api_key: str,
    posted_from: str,
    posted_to: str,
    naics_codes: Iterable[str],
    keywords: Iterable[str],
    limit_per_query: int = 100,
) -> list[dict]:
    """
    Runs one search per NAICS code and one per keyword (the API only accepts
    a single ncode/title value per call), then dedupes the combined results
    by noticeId. A failure on any single query is logged and skipped rather
    than aborting the whole pool.
    """
    by_notice_id: dict[str, dict] = {}

    def _ingest(results: list[dict]):
        for opp in results:
            notice_id = opp.get("noticeId")
            if notice_id and notice_id not in by_notice_id:
                by_notice_id[notice_id] = opp

    for naics in naics_codes:
        try:
            _ingest(
                search_opportunities(
                    api_key, posted_from, posted_to, naics=naics, limit=limit_per_query
                )
            )
        except Exception as exc:
            print(f"[sam_client] NAICS query {naics} failed: {exc}")
        time.sleep(INTER_QUERY_DELAY_SECONDS)

    for keyword in keywords:
        try:
            _ingest(
                search_opportunities(
                    api_key,
                    posted_from,
                    posted_to,
                    title_keyword=keyword,
                    limit=limit_per_query,
                )
            )
        except Exception as exc:
            print(f"[sam_client] keyword query '{keyword}' failed: {exc}")
        time.sleep(INTER_QUERY_DELAY_SECONDS)

    return list(by_notice_id.values())
