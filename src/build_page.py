"""Renders the ranked/summarized results into docs/index.html (GitHub Pages)."""

from __future__ import annotations

import html
from datetime import datetime

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAM.gov TLDR</title>
<style>
  :root {{
    --bg: #0b0d12; --panel: #12161f; --border: #232937; --text: #e8ebf1;
    --muted: #93a0b4; --accent: #5b8cff; --fun: #f2a13d;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{ --bg:#f6f7fb; --panel:#ffffff; --border:#e2e5ec; --text:#1a1d24; --muted:#5b6472; --accent:#3660d6; --fun:#b5670f; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2rem 1rem 4rem; background: var(--bg); color: var(--text);
    font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  }}
  .wrap {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
  .meta {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 1.5rem; }}
  .tldr {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.25rem; margin-bottom: 2rem; line-height: 1.5;
  }}
  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.25rem; margin-bottom: 1rem;
  }}
  .card.fun {{ border-color: var(--fun); }}
  .card h3 {{ margin: 0 0 0.35rem; font-size: 1.05rem; }}
  .card .tags {{ color: var(--muted); font-size: 0.8rem; margin-bottom: 0.5rem; }}
  .card p {{ margin: 0.35rem 0; line-height: 1.45; }}
  .card .why {{ color: var(--muted); font-size: 0.9rem; }}
  .card a {{ color: var(--accent); text-decoration: none; font-size: 0.9rem; }}
  .card a:hover {{ text-decoration: underline; }}
  .section-label {{
    text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.75rem;
    color: var(--muted); margin: 1.75rem 0 0.75rem;
  }}
  .empty {{ color: var(--muted); font-style: italic; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>SAM.gov TLDR</h1>
  <div class="meta">Generated {generated_at} &middot; Radiance / NASIC M&amp;S profile</div>
  <div class="tldr">{overall_tldr}</div>
  <div class="section-label">Top picks</div>
  {job_cards}
  <div class="section-label">For funzies</div>
  {fun_card}
</div>
</body>
</html>
"""

CARD_TEMPLATE = """<div class="card{fun_class}">
  <h3>{title}</h3>
  <div class="tags">{agency} &middot; NAICS {naics} &middot; {set_aside} &middot; posted {posted_date} &middot; due {response_deadline}</div>
  <p>{tldr}</p>
  <p class="why">{why_relevant}</p>
  <a href="{link}" target="_blank" rel="noopener">View on SAM.gov &rarr;</a>
</div>
"""


def _esc(value) -> str:
    return html.escape(str(value or "").strip()) or "&mdash;"


def _render_card(rec: dict, fun: bool = False) -> str:
    return CARD_TEMPLATE.format(
        fun_class=" fun" if fun else "",
        title=_esc(rec.get("title")),
        agency=_esc(rec.get("agency")),
        naics=_esc(rec.get("naics")),
        set_aside=_esc(rec.get("set_aside")),
        posted_date=_esc(rec.get("posted_date")),
        response_deadline=_esc(rec.get("response_deadline")),
        tldr=_esc(rec.get("tldr")),
        why_relevant=_esc(rec.get("why_relevant")),
        link=html.escape(str(rec.get("link") or "#"), quote=True),
    )


def render_page(result: dict, generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.utcnow()
    job_recs = result.get("job_recommendations") or []
    fun_rec = result.get("fun_recommendation")

    job_cards = (
        "".join(_render_card(r) for r in job_recs)
        if job_recs
        else '<p class="empty">No matching opportunities found in this run.</p>'
    )
    fun_card = (
        _render_card(fun_rec, fun=True)
        if fun_rec
        else '<p class="empty">Nothing fun turned up this time.</p>'
    )

    return PAGE_TEMPLATE.format(
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M UTC"),
        overall_tldr=_esc(result.get("overall_tldr")) or "No summary available.",
        job_cards=job_cards,
        fun_card=fun_card,
    )


def write_page(result: dict, out_path: str = "docs/index.html") -> None:
    html_content = render_page(result)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
