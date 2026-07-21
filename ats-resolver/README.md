# ats-resolver

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

### Why Workday is deliberately out of scope

The four supported providers expose public, unauthenticated JSON APIs intended for exactly this use. Workday does not: reading it means hitting an undocumented per-tenant endpoint whose tenant, site, and datacenter are not discoverable from a company name. There is no public API contract, and per-tenant endpoints are not a stable interface, so a Workday provider would be the least reliable component pretending to be a tier-1 source. It is excluded on purpose; a Workday careers link found by the scraper is still surfaced so a human can follow it.

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
cd ats-resolver
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell; Git Bash: . .venv/Scripts/activate; macOS/Linux: . .venv/bin/activate
pip install -r requirements.txt
```

## Connect to an MCP client

Add to your MCP config (adjust the python path to the venv you installed into):

```json
{
  "mcpServers": {
    "ats-resolver": {
      "command": "python",
      "args": ["-m", "ats_resolver_mcp.server"],
      "cwd": "/path/to/ats-resolver"
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
cd ats-resolver
python -m pytest -q
```

## Extending (registry pattern)

Add a provider by implementing `ATSProvider` (detect / from_url / list_jobs) in `ats_resolver_mcp/providers/` and registering it in `providers/registry.py`. Parse logic lives in module-level pure functions so new providers get fixture tests for free.

## Limitations

- Providers change payload shapes. The four vendor APIs are public but not versioned contracts; a schema change breaks parsing until the provider is updated, which is why parse logic is isolated in pure functions with fixture tests.
- Slug detection guesses board tokens from the company name. When a company registered a non-obvious slug, pass a hint_url (the aggregator redirect usually provides one).
- The careers-page scraper is best-effort and intentionally last in the chain. It is a single-page, low-volume read used only when no ATS API answers; it never crawls, and it is designed for use that respects site policies (robots directives and terms of service).
- Remote-status inference is only as good as the posting text. A posting that never states its arrangement resolves to `unknown` / `ambiguous`, by design; the tool reports uncertainty rather than manufacturing an answer.
- Live endpoint behavior can drift; the bundled tests validate parsing against committed fixtures, not the live services.
