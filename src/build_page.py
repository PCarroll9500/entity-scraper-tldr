"""
Renders the ranked/summarized results into docs/index.html (GitHub Pages).

Styled to match pcarroll9500.github.io (the resume site): same w3.css card
look, Roboto font, blue/grey color language, icon-led headers, dark diagonal
canvas background, and entries grouped inside one card and separated by
<hr> rather than each being its own boxed card.
"""

from __future__ import annotations

import html
from datetime import datetime

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAM.gov TLDR</title>
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<link rel='stylesheet' href='https://fonts.googleapis.com/css?family=Roboto'>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
<style>
  html, body, h1, h2, h3, h4, h5, h6 {{ font-family: "Roboto", sans-serif; }}
  body {{ font-size: 20px; line-height: 1.55; }}
  canvas#pattern {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; }}
  .topnav {{ background-color: #4994ec; overflow: hidden; }}
  .topnav a {{
    float: left; color: #f2f2f2; text-align: center; padding: 14px 18px;
    text-decoration: none; font-size: 18px;
  }}
  .topnav a.active {{ background-color: #0449aa; color: white; }}
  .topnav a:hover {{ background-color: #ddd; color: black; }}

  /* Explicit fallback colors (not just w3-white/w3-text-grey) so cards stay
     readable even if the w3.css CDN is slow/blocked. */
  .card-box {{
    background-color: #ffffff !important; color: #333333;
    box-shadow: 0 2px 6px rgba(0,0,0,0.35); border-radius: 2px;
  }}
  .card-box h2 {{
    color: #757575; padding: 1rem 1.5rem 0.5rem; font-size: 1.7rem; margin: 0;
  }}
  .card-box h2 i {{ color: #4994ec; }}
  .entry {{ padding: 0 1.5rem 1.25rem; }}
  .entry h4 {{ color: #333333; font-size: 1.4rem; margin: 0 0 0.4rem; }}
  .entry .meta-line {{
    color: #333333; font-size: 1.05rem; margin: 0.3rem 0; font-style: normal;
  }}
  .entry .meta-line i {{ color: #4994ec; }}
  .entry .tldr-body {{ font-size: 1.2rem; line-height: 1.55; margin: 0.75rem 0; color: #333333; }}
  .entry .why {{
    font-size: 1.05rem; line-height: 1.5; border-left: 4px solid #4994ec;
    padding-left: 1rem; margin: 0.9rem 0; color: #555555;
  }}
  .entry.fun .why {{ border-left-color: #f2a13d; }}
  .entry .tag {{ background-color: #4994ec !important; color: #fff !important; }}
  .entry a.w3-button {{ background-color: #4994ec !important; color: #ffffff !important; }}
  .sidebar p {{ font-size: 1.05rem; }}
  .sidebar p i {{ color: #4994ec; }}
  .section-hr {{ border: none; border-top: 1px solid #ddd; margin: 0 1.5rem; }}
  .empty {{ font-style: italic; font-size: 1.1rem; color: #333333; padding: 0 1.5rem 1.5rem; }}
</style>
</head>
<body>

<canvas id="pattern"></canvas>
<script>
  var canvas = document.getElementById('pattern');
  var ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  ctx.fillStyle = '#333333';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#ffffff';
  for (var i = 0; i < canvas.width; i += 50) {{
    for (var j = 0; j < canvas.height; j += 50) {{
      if (Math.random() < 0.5) {{
        ctx.beginPath();
        ctx.moveTo(i, j);
        ctx.lineTo(i + 25, j + 25);
        ctx.stroke();
      }}
    }}
  }}
</script>

<div class="topnav">
  <a href="https://pcarroll9500.github.io/">Home</a>
  <a class="active" href="#">SAM.gov TLDR</a>
</div>

<div class="w3-content w3-margin-top" style="max-width:1400px;">
  <div class="w3-row-padding">

    <!-- Left column -->
    <div class="w3-third">
      <div class="card-box sidebar">
        <div class="w3-container" style="padding: 1.5rem;">
          <h2 style="padding:0 0 0.75rem;"><i class="fa fa-flash fa-fw w3-margin-right"></i>SAM.gov TLDR</h2>
          <p><i class="fa fa-briefcase fa-fw w3-margin-right w3-large"></i>Radiance Technologies &middot; NASIC M&amp;S</p>
          <p><i class="fa fa-map-marker fa-fw w3-margin-right w3-large"></i>Dayton, OH</p>
          <p><i class="fa fa-refresh fa-fw w3-margin-right w3-large"></i>Updated {generated_at}</p>
          <p><i class="fa fa-bullseye fa-fw w3-margin-right w3-large"></i>{num_job} job picks &middot; 1 for funzies</p>
        </div>
      </div>
      <br>
    </div>
    <!-- End left column -->

    <!-- Right column -->
    <div class="w3-twothird">

      <div class="card-box w3-margin-bottom">
        <h2><i class="fa fa-file-text-o fa-fw w3-margin-right"></i>Today's TLDR</h2>
        <div class="entry" style="padding-top:0.5rem;">
          <p class="tldr-body" style="font-size:1.3rem;">{overall_tldr}</p>
        </div>
      </div>

      <div class="card-box w3-margin-bottom">
        <h2><i class="fa fa-star fa-fw w3-margin-right"></i>Top Picks</h2>
        <hr class="section-hr">
        {job_entries}
      </div>

      <div class="card-box w3-margin-bottom">
        <h2><i class="fa fa-smile-o fa-fw w3-margin-right" style="color:#f2a13d;"></i>For Funzies</h2>
        <hr class="section-hr">
        {fun_entry}
      </div>

    </div>
    <!-- End right column -->

  </div>
</div>

<footer class="w3-container w3-blue w3-center w3-margin-top w3-padding-32">
  <p>Part of <a href="https://pcarroll9500.github.io/" style="color:white; text-decoration:underline;">pcarroll9500.github.io</a></p>
  <p>Powered by <a href="https://www.w3schools.com/w3css/default.asp" target="_blank" style="color:white;">w3.css</a></p>
</footer>

</body>
</html>
"""

ENTRY_TEMPLATE = """<div class="entry{fun_class}">
  <h4><b>{title}</b></h4>
  <p class="meta-line"><i class="fa fa-building fa-fw w3-margin-right"></i>{agency}</p>
  <p class="meta-line"><i class="fa fa-calendar fa-fw w3-margin-right"></i>NAICS {naics} &middot; {set_aside} &middot; posted {posted_date}
    <span class="w3-tag tag w3-round">due {response_deadline}</span>
  </p>
  <p class="tldr-body">{tldr}</p>
  <p class="why"><i>{why_relevant}</i></p>
  <a href="{link}" class="w3-button w3-round" target="_blank" rel="noopener">
    <i class="fa fa-external-link fa-fw"></i> View on SAM.gov
  </a>
</div>
<hr class="section-hr">
"""


def _esc(value) -> str:
    return html.escape(str(value or "").strip()) or "&mdash;"


def _render_entry(rec: dict, fun: bool = False) -> str:
    return ENTRY_TEMPLATE.format(
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

    job_entries = (
        "".join(_render_entry(r) for r in job_recs)
        if job_recs
        else '<p class="empty">No matching opportunities found in this run.</p>'
    )
    fun_entry = (
        _render_entry(fun_rec, fun=True)
        if fun_rec
        else '<p class="empty">Nothing fun turned up this time.</p>'
    )

    return PAGE_TEMPLATE.format(
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M UTC"),
        num_job=len(job_recs),
        overall_tldr=_esc(result.get("overall_tldr")) or "No summary available.",
        job_entries=job_entries,
        fun_entry=fun_entry,
    )


def write_page(result: dict, out_path: str = "docs/index.html") -> None:
    html_content = render_page(result)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
