# entity-scraper-tldr

Pulls new [SAM.gov](https://sam.gov) federal contract opportunities via the
official public API, filters them down to two pools, and uses OpenAI to
produce a daily TLDR page: **9 job-related picks + 1 "for funzies" pick**,
published to GitHub Pages.

- **Job pool**: Modeling & Simulation / NASIC / Air Force-flavored work
  (relevant to Radiance Technologies / NASIC M&S).
- **Hobby pool**: small hobby-software, basic electrical/cabling, and
  hauling/trucking jobs.

Tune both pools' NAICS codes and keywords in [`src/config.py`](src/config.py).

## How it works

1. `src/sam_client.py` queries the [SAM.gov Get Opportunities API v2](https://open.gsa.gov/api/get-opportunities-public-api/)
   (one call per NAICS code + one per keyword, per pool), dedupes by
   `noticeId`, and fetches full descriptions for a capped subset of each pool.
2. `src/summarize.py` sends the compact candidate pools to OpenAI
   (`gpt-4o-mini` by default -- see cost note below) in a **single** chat
   completion call, asking for the 9 best job-pool matches and 1 fun
   hobby-pool pick, each with a short TLDR + relevance note.
3. `src/build_page.py` renders the result into `docs/index.html`.
4. A GitHub Actions workflow (`.github/workflows/update.yml`) runs this daily,
   commits the updated page + raw data snapshot, and deploys `docs/` to
   GitHub Pages.

## Setup

1. **Get a SAM.gov API key** (free): log into [sam.gov](https://sam.gov),
   go to your account profile > **Data Services**, and request an API key.
2. **Get an OpenAI API key**: https://platform.openai.com/api-keys
3. Add both as repo secrets: **Settings > Secrets and variables > Actions**
   - `SAM_API_KEY`
   - `OPENAI_API_KEY`
4. Enable GitHub Pages: **Settings > Pages > Source: GitHub Actions**
   (the workflow deploys `docs/` automatically -- no branch config needed).
5. Run the workflow once manually (**Actions > Update SAM.gov TLDR > Run
   workflow**) to generate the first page, or run it locally:

   ```bash
   pip install -r requirements.txt
   cp .env.example .env   # fill in your keys
   python src/main.py
   ```

The page updates automatically every day at 12:00 UTC (see the `cron` line
in the workflow -- adjust to taste, SAM.gov posts on business days).

## Cost notes

- SAM.gov's public API is free.
- OpenAI usage is a single small chat completion per run using `gpt-4o-mini`
  (cheap). Override the model via the `OPENAI_MODEL` env var / secret if you
  want higher quality at higher cost, but the default is intentionally
  budget-friendly for a daily digest job.

## Caveats

- SAM.gov API field names/behavior were implemented from the published API
  docs without a live key to test against -- if a field comes back empty or
  a query errors, check `data/latest_raw.json` after a run and adjust
  `src/sam_client.py` / `src/config.py` as needed.
- This only ever calls the official SAM.gov API -- it does not scrape the
  sam.gov website.
