# job-posting-resolver

A multi-provider job-posting resolver: an entity-resolution and data-reliability tool packaged as a local MCP server. It was built to answer one question reliably (is this role actually remote) by going to the authoritative source instead of trusting aggregator metadata.

```
aggregator hit (job board, search index, etc.)
   -> ATS  (Greenhouse | Lever | Ashby | SmartRecruiters)
   -> company careers page  (last-resort HTML scrape)
```

## The problem

Job-board aggregators stamp a posting with the company HQ and a noisy `is_remote` flag, because remote-eligibility lives in a separate ATS field the board indexes weakly. The truth is on the live Applicant Tracking System listing. This is a small instance of a general alternative-data problem: the convenient feed is a lossy derivative of the system of record, and the fix is to resolve each record back to its authoritative source and be explicit about how much you trust each field.

## Reliability hierarchy (the mechanism)

Not all reads are equal. The chain is ordered by reliability, highest first:

1. **Authoritative ATS API fields** (public JSON APIs, no auth, no scraping): Lever exposes `workplaceType`, Ashby `isRemote`, SmartRecruiters `location.remote`. When the vendor states the work arrangement in a dedicated field, that value wins.
2. **Inferred fields**: Greenhouse has no dedicated remote flag in its list schema, so work arrangement is inferred from location text ("Remote - US") and, on detail reads, the description. Inference is labeled as such; a bare city resolves to `unknown`, never to a guess.
3. **Scraped fallback** (HTML): lowest reliability, used only when no ATS is detected. Returns an inferred arrangement plus any links that point back to an ATS, so the caller can pivot to an authoritative read.

Every provider normalizes into one canonical `Posting` model, so the caller never has to know which ATS a listing came from.

### iCIMS and Workday (added 2026-07-25, tier 2 by design)

Both were previously out of scope. A live coverage measurement changed that: across a 90-company scan, 49 companies could not be resolved at all, and the two platforms accounted for most of them. Excluding them was not neutrality, it was a silent hole.

They are deliberately last in the detection chain and are honest about being weaker reads than the four JSON APIs.

**iCIMS** exposes no public JSON API, so this is an HTML read of the compact iframe view of the public board (`/jobs/search?ss=1&in_iframe=1`). Board tokens are predictable (`careers-{token}.icims.com`), so detection works from a company name. Rows carry labelled `Job Locations` and `Title` fields, which is enough for title, location, id and url; there is no posted date and no department. Pagination is hard-capped at 12 pages and stops as soon as a page repeats or under-fills, so it reads a listing page and never crawls.

**Workday** does expose a usable public endpoint, the CXS job-search API (`POST /wday/cxs/{tenant}/{site}/jobs`), which returns title, location text, posted-on string and an external path. The real obstacle was never the payload, it is the address: a board is identified by three unknowns (tenant, `wdN` shard, and site name), and guessing all three from a company name is unreliable. So `from_url` is exact and is the intended path, while `detect` runs a deliberately small best-effort matrix over the most common shards and site names and gives up rather than probing dozens of URLs. When it fails it now says UNRESOLVED, which is the honest answer.

The original objection still holds and is worth keeping in mind: neither is a published API contract, so both are more likely to break than the tier-1 four. That is why they sit last, why their parse logic is isolated in pure functions with fixture tests, and why a low-confidence result from either reports as unresolved rather than empty.

## Tools

| Tool | Purpose |
|------|---------|
| `ats_resolve` | Detect which ATS a company uses (+ board token). Accepts a hint_url for exact, instant resolution. |
| `ats_list_jobs` | List live postings (normalized), with optional title and location filters. |
| `ats_get_job` | Full detail for one posting, including the work-arrangement line. |
| `ats_verify_remote` | One-shot: is a named role remote / hybrid / onsite? Returns a verdict. |
| `ats_scrape_careers_page` | Last-resort HTML read when no ATS API is detected. |

`ats_verify_remote` verdicts:

- `remote-eligible`: the posting states a fully remote arrangement
- `hybrid` / `onsite`: the posting states a hybrid or onsite arrangement
- `ambiguous`: arrangement not stated; verify manually
- `not-found`: no title match on the board
- `unresolved`: no ATS detected; try a hint_url or `ats_scrape_careers_page`

## Install

```
cd job-posting-resolver
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell; Git Bash: . .venv/Scripts/activate; macOS/Linux: . .venv/bin/activate
pip install -r requirements.txt
```

## Connect to an MCP client

Add to your MCP config (adjust the python path to the venv you installed into):

```json
{
  "mcpServers": {
    "job-posting-resolver": {
      "command": "python",
      "args": ["-m", "ats_resolver_mcp.server"],
      "cwd": "/path/to/job-posting-resolver"
    }
  }
}
```

The server speaks stdio (local, single-user). It makes outbound HTTPS calls to public ATS endpoints at runtime; no API keys are required.

## Usage examples

All company names below are fictional.

- Verify a flagged role:
  `ats_verify_remote(company="Acme Analytics", title="Market Research Analyst")`
- If the aggregator gave you the ATS redirect link, pass it for an exact read:
  `ats_verify_remote(company="Fogline Data", title="Senior Customer Insights Analyst", hint_url="https://boards.greenhouse.io/foglinedata/jobs/123")`
- Browse a company's whole board:
  `ats_list_jobs(company="Pinebrook Insights", query="insights")`
- No ATS detected, fall back:
  `ats_scrape_careers_page(url="https://example.com/careers")`, then re-run `ats_resolve` with any ATS link it surfaces.

## Tests

21 fixture-based unit tests, offline (no network). Every fixture is a synthetic payload for a fictional company, shaped like the real vendor schemas:

```
cd job-posting-resolver
python -m pytest -q
```

## Extending (registry pattern)

Add a provider by implementing `ATSProvider` (detect / from_url / list_jobs) in `ats_resolver_mcp/providers/` and registering it in `providers/registry.py`. Parse logic lives in module-level pure functions so new providers get fixture tests for free.

## Disclosed fixes

**2026-07-25, the empty-envelope false negative (found in live use, not by the test suite).**

All four providers detected a board by checking that the response *envelope* was well formed, for example `"content" in data` or `"jobs" in data`, never that it contained anything. Several of these APIs answer HTTP 200 with a valid but empty payload for a slug that does not exist. SmartRecruiters returns `{"content": [], "totalFound": 0}` for literally any string, verified against a nonsense slug returning byte-identical output to four real companies.

Because SmartRecruiters is probed last, it acted as a catch-all: every company the first three could not resolve was "resolved" to a SmartRecruiters board that was never real, and `ats_list_jobs` then reported **"No postings matched"**, which reads as *this company has no openings* rather than *the lookup failed*. In a live target-list run this produced silent false negatives on Comscore, Parrot Analytics, Numerator, Placer.ai, Vista Equity Partners, and SailPoint. A false negative is worse than an error here, because an error prompts a retry and an empty result ends the search.

The fix, in three parts. Providers now record `observed_count` from the detection probe and set `confidence` to `high` or `low`. The registry no longer stops at the first shape-valid answer; an empty hit is held as a fallback while the rest of the chain is probed, so a real board with postings always wins over an empty envelope. And a low-confidence board reports `UNRESOLVED` with next steps rather than an empty result set.

An empty board is still returned rather than discarded, because a real company can legitimately have zero openings. The distinction the caller needs is *unresolved* versus *empty*, and that distinction is now carried explicitly instead of being collapsed.

Six regression tests cover it (`tests/test_providers.py`), including the registry preferring a populated board over an empty one and the all-empty case still returning low confidence.

## Limitations

- Providers change payload shapes. The four vendor APIs are public but not versioned contracts; a schema change breaks parsing until the provider is updated, which is why parse logic is isolated in pure functions with fixture tests.
- Slug detection guesses board tokens from the company name. When a company registered a non-obvious slug, pass a hint_url (the aggregator redirect usually provides one).
- The careers-page scraper is best-effort and intentionally last in the chain. It is a single-page, low-volume read used only when no ATS API answers; it never crawls, and it is designed for use that respects site policies (robots directives and terms of service).
- Remote-status inference is only as good as the posting text. A posting that never states its arrangement resolves to `unknown` / `ambiguous`, by design; the tool reports uncertainty rather than manufacturing an answer.
- Live endpoint behavior can drift; the bundled tests validate parsing against committed fixtures, not the live services.
