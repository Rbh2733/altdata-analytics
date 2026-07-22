"""ats_resolver_mcp: resolve a company's ATS and verify role work arrangement.

Job-board aggregators stamp postings with unreliable location metadata; the company's
Applicant Tracking System (ATS) is the source of truth. This MCP server sits between
an aggregator hit and the company site:

    aggregator hit -> ATS (Greenhouse / Lever / Ashby / SmartRecruiters)
                   -> company careers page (last resort, HTML scrape)

The authoritative work arrangement (remote / hybrid / onsite) lives on the live ATS
listing, not on the aggregator. This server reads that authoritative field through
public, unauthenticated JSON APIs, with an explicit reliability hierarchy:
authoritative ATS fields first, inferred fields second, scraped HTML last.
"""

__version__ = "0.1.0"
