# Layer 7: Identity Resolution & Clean Rooms (Master Findings)

> **Document type:** Master findings file (Deep Research integration), not a prompt file and not the diff map.
> **Created:** 2026-07-08, integration pass
> **Sources:** two unlabeled Gemini passes, Run 01 (2026-07-07 12:09 UTC) and Run 02 (12:18 UTC, roughly 9 minutes later)
> **Base document:** Run 02 for the Publicis/LiveRamp section, per `DEEP-RESEARCH-DIFF-MAP.md` Section 8
> **Readiness:** merged, three fault lines resolved, one item flagged single-source, one gap remains genuinely open

---

## 1. Findings by research objective

**1. LiveRamp/Publicis deal status.** Both passes confirm the same core terms: $38.50 per share, a 29.8% premium, $2.167 billion enterprise value / $2.546 billion equity value, an August 17, 2026 shareholder vote, HSR/CFIUS pending, still pending, not closed. Run 01 is stronger on deal mechanics and the regulatory timeline: a $32.35 million break fee, HSR filed June 11, 2026, and a Johnson Fistel investigation. Run 02 is far stronger on client-attrition commentary, naming WPP CEO Cindy Rose's on-record Cannes Lions confirmation of a full exit to InfoSum, and Omnicom's planned Q1 2028 exit to its own Real ID, both absent from Run 01. Neither pass re-verified deal status was still current as of its own research date; that check was done separately (see Gaps remaining) against Publicis Groupe's own press release, confirming nothing has changed.

**2. UID2 trajectory and The Trade Desk's reaction.** Run 01 covers UID2 scale (200-plus publishers) and, uniquely, the full Publicis-TTD audit dispute (a fee-stacking allegation, a 13% stock hit, resolved June 12). Run 02 covers the same June 12 reaffirmation but omits the dispute backstory, adding unique detail on TTD's Kokai/Koa Agents and its Open Agentic Kit (Anthropic Claude integration). Combined, this objective is complete.

**3. AMC versus Walmart Connect economics.** Both passes attempt AMC-specific quantification but diverge (Section 4). Neither cites a true AMC-only revenue line; both proxy with total Amazon ad revenue.

**4. New entrants and agentic identity protocols.** Complementary coverage. Run 01 covers commerce-transaction protocols (UCP, ACP, MCP). Run 02 covers agent-identity/auth protocols (AgentID/IETF draft, OAuth 2.1 PKCE, SPIFFE/SPIRE, Ping's "Identity for AI") plus Omnicom's disclosed direct-to-publisher AI agent buys.

**5. Comscore CustomIQ.** Both passes corroborate the recap, McLaughlin/Frankel, and the 99.5% match rate. Run 02 uses the rubric's own language and adds the Movies divestiture and an 89.8% email-only match rate. Run 01 adds an AI-assistant traffic table not present in Run 02.

---

## 2. Corroborated across both variants

$38.50 per share, a 29.8% premium (versus a $29.66 close, May 15, 2026), $2.167 billion enterprise value / $2.546 billion equity value, a 66 2/3% shareholder-vote threshold, an August 17, 2026 special meeting, an Evercore fairness opinion, HSR/CFIUS required, target close by end of 2026. WPP-InfoSum (April 2025) and Omnicom-IPG/Acxiom (2025) consolidation. Comscore's recap closed December 29, 2025 ($18 million dividend eliminated). Matt McLaughlin (ex-DoubleVerify COO) as CEO, Stuart Frankel to the board. CustomIQ's 99.5% Full-PII match-rate validation of LiveRamp. The June 12, 2026 Publicis-TTD reaffirmation.

---

## 3. Additional detail pulled in from Run 01 (per the recommended integration approach)

Run 02 is the base for the Publicis/LiveRamp section given its stronger sourcing on client attrition, the objective the prompt file flagged as highest priority, and on deal financing. Pulled forward from Run 01: the TTD audit-dispute narrative, which contextualizes the June 12 reaffirmation as a resolution rather than a steady state; the Johnson Fistel investigation; the HSR filing date and break fee; and the AI-assistant traffic table for the Comscore section.

Run 02's own unique material, beyond what's folded into Section 1: the financing structure (bonds, 1.2x leverage, $126 million EBITDA, $50 million in synergies, BBB+/Baa1 ratings), shares outstanding (60,786,315), named WPP/Omnicom/ID5/CleanTap/Ray Media/Unity CRO reactions, and Omnicom's disclosed AI-agent media buys.

For deal terms specifically, Publicis Groupe's own press release (publicisgroupe.com, 2026-05-17) confirms both passes' $2.167 billion enterprise value / $2.546 billion equity value / $38.50 per share / 29.8% premium figures exactly; use it as the anchor citation over either individual pass.

---

## 4. Fault lines

**Resolved:**

Amazon's total advertising revenue. Run 01 says TTM greater than $70 billion (Q1 2026 $17.2 billion). Run 02 says ">$50 billion annually in 2026, up from $38 billion in 2023." Verified directly against Amazon's own Q1 2026 earnings release (Andy Jassy's own quote: "Advertising grew to over $70 billion in TTM revenue," Q1 2026 ad revenue $17.24 billion, +24% year over year): Run 01 is correct and current, Run 02 is stale by roughly $20 billion. Same conflict as the Layer 0 file's review, resolved there once and cross-referenced here rather than re-litigated.

Walmart Connect revenue. Run 01 gives FY2025 figures of "$4.4 billion US / $6.4 billion global (+24%/+46%)." Run 02 and the Layer 4 Pro docx both give ">$4.8 billion in 2025 (+30% YoY)" with no US/global split. Checked against Walmart's own SEC 8-K earnings releases and earnings-presentation exhibits for both fiscal years (FY25 8-K, sec.gov/Archives/edgar/data/0000104169/000010416925000010; FY26 8-K, sec.gov/Archives/edgar/data/0000104169/000010416926000095, corroborated by Marketing Dive, AdExchanger, and Adweek coverage of the same releases): actual reported figures are FY2025 global ad revenue $4.4 billion (+27% full year; Walmart's fiscal year ends January 31), and FY2026 global ad revenue $6.4 billion (+46% year over year), with Q4 FY2026 US Walmart Connect growth of 41%. Run 01's $4.4 billion figure is real but mislabeled, it's FY25 global, not US, revenue. Run 01's $6.4 billion figure is real but misdated, it belongs to FY26, not FY25. Run 02's $4.8 billion figure doesn't match either fiscal year's disclosure and should be dropped. Use the corrected pairing: FY25 global $4.4 billion (+27%), FY26 global $6.4 billion (+46%, Q4 US Walmart Connect +41%), both cited to Walmart's own SEC filings rather than either pass's secondary-blog citation.

AMC free-tier mechanics. Run 01 says first-party signals are free June 1 through December 31, 2026 (a time-limited promotion). Run 02 says free on an ongoing basis for any advertiser with an active DSP MSA, no expiration stated. Confirmed directly against Amazon's own AMC documentation page (advertising.amazon.com, "Paid features overview"): "Starting June 1, 2026, all Amazon 1P signals covered under AMC Paid Features...will be available to query at no cost through December 31, 2026 in all regions where AMC Paid Features are available." Run 01 is correct, this is an explicitly time-limited promotion with a stated end date, not a permanent MSA-conditioned policy. Run 02 is wrong on the framing (permanent versus promotional) even though its underlying point, that eligible advertisers don't pay extra right now, is directionally true for the remainder of 2026. Use Run 01's framing and the December 31, 2026 sunset date, and flag it as a date to revisit since the promotion's fate after that isn't stated on the page.

**Flagged, not resolved:**

The deal-financing detail in Run 02 (leverage, EBITDA, synergies) is entirely uncorroborated by Run 01. Flag as single-source pending a second check before treating any individual figure in it as settled.

---

## 5. Gaps remaining

Deal status was re-confirmed 2026-07-07 and is no longer an open gap in the narrow sense: signed 2026-05-17, not yet closed, still subject to regulatory approval and a LiveRamp shareholder vote, targeted to close before year-end 2026, per Publicis Groupe's own press release, with no reported change in terms, competing bid, or regulatory objection as of that check.

No pass isolates a true AMC-only revenue figure. That gap remains genuinely open and was not independently verified in this integration pass.

---

## 6. Provenance

Synthesized from `DEEP-RESEARCH-DIFF-MAP.md` Section 8 (two unlabeled Gemini passes, 2026-07-07). No new research performed in this integration pass beyond the primary-source checks already logged in the diff map (Amazon's Q1 2026 earnings release, Walmart's SEC 8-K filings, Amazon's AMC documentation page, Publicis Groupe's own press release). Fault-line convention follows `streaming-altdata-ecosystem.md` Section 6.
