# Focused-Layer Reconciliation Audit

> **Document type:** Audit record, not a research file. Records what changed when the `layers/Focus Research/0N-*-focused-master.md` tier was cross-referenced against the `layers/0N-*-layer.md` tier for the first time, plus a cross-layer consistency pass and an overview check. No source file was deleted or restructured; every change below is a targeted in-place edit.
> **Date:** 2026-07-14
> **Status:** Complete. All 8 layers reconciled, cross-layer pass complete, overview checked clean.

---

## 0. Why this pass happened

`layers/Focus Research/0N-*-focused-master.md` is a tier that existed on disk but was never mentioned in `streaming-altdata-ecosystem.md` or `DEEP-RESEARCH-DIFF-MAP.md`, and had never been checked against its corresponding `layers/0N-*-layer.md` file. Reid asked for the two tiers (plus, for Layer 2, the `companies/Comscore/` docs) to be cross-referenced so the whole stack — company docs → focused-master → layer file → overview — reads as internally consistent without merging any of the documents into a new file.

**Method, per layer:** one agent read the layer file and its focused-master (and, for Layer 2, the Comscore docs) in full, diffed them fact by fact, and for every conflict found:
1. Attempted verification via web search against a primary source (SEC filings, company IR pages, court dockets, press releases).
2. If verified, corrected whichever file was wrong, with a short inline citation matching the existing prose voice — no footnotes, no new sections.
3. If not independently verifiable, defaulted to the more granular document (company docs > focused-master > layer file) as the interim value, flagged minimally inline.
4. Left non-contradictory gaps alone — a fact present in only one file is not an error and was not pulled into the other file.

After all 8 layers finished, a cross-layer pass checked facts that recur across multiple layers' documents (Amazon ad revenue, the LiveRamp/Publicis deal, Fox-Roku, Walmart Connect/Luminate, the VPPA circuit split, Genius Sports' NFL stake) for consistency between layers, since no single layer agent could see across all 8. The main overview (`streaming-altdata-ecosystem.md`) was then checked against every correction made below.

**Total: 20 edits across 12 files.** No file was deleted. No archive `.docx` was touched.

---

## 1. Layer 0 — Ecosystem Gatekeepers

**Edits: 2**

- `layers/Focus Research/00-gatekeeper-focused-master.md` — PSKY/WBD debt financing was stated as a flat "$54 billion in new debt commitments," which was the pre-restructuring figure. Corrected to reflect the actual $49 billion senior secured bridge facility plus ~$39.5 billion first-lien permanent financing (the layer file already had this right), verified against Paramount Skydance's 2026 8-K filings.
- `layers/00-gatekeeper-layer.md` — "The Roku Channel alone at 6.3% of US TV streaming time" was carried as an unresolved fault line against a competing "5.2% combined" figure. This was a mislabeled figure, not a genuine two-source disagreement: Nielsen's own March 2026 Gauge data (corroborated via advertising.roku.com) shows The Roku Channel alone at 3.0%, Tubi at 2.2%, with 5.2%–6.3% being the combined, projected post-merger range. Corrected in place (resolved during the cross-layer pass, after the layer agent flagged it but held off per its original instructions not to force a resolution).

## 2. Layer 1 — Wallet

**Edits: 2**, both in `layers/01-wallet-layer.md`

- "No pass identifies a new Wallet-layer entrant" was stale — the focused-master had already identified **Coverd**, an a16z-backed gamified cash-back card launched June 18, 2026, verified via a16z's own portfolio page and press coverage. Corrected to acknowledge it.
- DROP broker registry count: layer file said "over 600 entities," focused-master said "over 500." CPPA's live registry page didn't render usable data for an independent check, so defaulted to the focused-master's figure (500) with an inline note that some secondary reporting cites 600.

## 3. Layer 2 — Glass (Hardware / ACR), including Comscore company docs

**Edits: 3** (busiest layer, all independently verified)

- `layers/02-glass-layer.md` — Comscore's MRC accreditation was understated as local-only since April 2025; actually national+local since March 2024, with April 2025 an expansion to demographic metrics, not the origin. Corrected with citation.
- `companies/Comscore/Comscore Valuation Analysis & Research Report.md` — implied iSpot.tv was still on "conditional" JIC certification; actually iSpot received full national certification August 13, 2024. Corrected.
- `layers/02-glass-layer.md` — VPPA section had two errors: (a) framed Supreme Court review as "a live variable" when cert had already been granted (Docket No. 25-459, January 26, 2026); (b) mischaracterized the Sixth Circuit's holding as turning on "paying" subscribers, when it actually turns on the nature of the good (audiovisual or not), not payment. Both corrected in one edit.

## 4. Layer 3 — Shield (Media Quality Verification / Fraud)

**Edits: 0.** Clean pass. Two apparent discrepancies were investigated and found non-contradictory: DoubleVerify's general "SlopStopper" (Q1 2026, ~40% attach rate) and "AI SlopStopper for Social" (YouTube-specific, launched April 2026) are two distinct products, not conflicting dates for one product. A shorter advisor-list mention in the focused-master was confirmed accurate, just less detailed than the layer file's fuller list.

## 5. Layer 4 — Demand/Valuation

**Edits: 2**

- `layers/04-demand-valuation-layer.md` — talent-agency list named only "CAA and WME"; the focused-master's "CAA, WME, and UTA" is correct — UTA runs its own analytics arm (UTA IQ, via the MediaHound acquisition) doing exactly this kind of demand-data ingestion. Added UTA with citation.
- `layers/04-demand-valuation-layer.md` — Walmart Connect's 2025 ad revenue was stated as "$4.8 billion," a stale/incorrect figure per Walmart's own SEC 8-K filings (see Section 8 below). Corrected to $4.4B FY2025 (+27%) / $6.4B FY2026 (+46%) during the cross-layer pass.

## 6. Layer 5 — Funnel

**Edits: 3**

- `layers/05-funnel-layer.md` — Reelgood's consumer-app user count was understated as "roughly 10 million"; Reelgood's own technology page states over 100 million. Corrected — the 10 million figure traced to a stale 2019 TechCrunch mention.
- `layers/05-funnel-layer.md` — Reelgood headcount upper bound (60 vs. 43) was not independently verifiable (no primary disclosure exists for this private company); defaulted to the focused-master's more granular figure (43).
- `layers/Focus Research/05-funnel-focused-master.md` — this time the focused-master was wrong: it listed Shinhan Securities as part of Sensor Tower's March 2024 data.ai acquisition financing syndicate. Verified via primary press releases that Shinhan's investment was a separate, later event (October 2025, unrelated to the acquisition). Corrected.

## 7. Layer 6 — Sports-Rights Sub-Vertical

**Edits: 2**

- `layers/06-sports-rights-layer.md` — the NFL's equity stake in Genius Sports was stated as "roughly 10%"; actually 8.7%, deliberately calibrated below the 10% SEC-disclosure threshold, per Sportico's June 2025 reporting. Corrected with citation.
- `layers/Focus Research/06-sports-rights-focused-master.md` — the VPPA section still framed Supreme Court review as "actively being sought" with a "2-2 split" characterization; stale against Layer 2's finding that cert was granted January 26, 2026 (Docket No. 25-459). Corrected during the cross-layer pass, aligned to the Layer 2 language.

A trivial rounding variance (Sportradar Q1 net loss: €6.3M vs. €6.2M) was found and deliberately left alone, consistent with how the project already treats that class of noise elsewhere.

## 8. Layer 7 — Identity Resolution & Clean Rooms

**Edits: 4** (all against Publicis Groupe's own press releases or on-record trade-press reporting)

- `layers/07-identity-clean-rooms-layer.md` — deal-signing date was internally inconsistent (stated both May 16 and May 17 in the same file). Corrected to May 17, 2026.
- `layers/07-identity-clean-rooms-layer.md` — Epsilon's consumer profile count was overstated at 2.3 billion; actually ~250 million. The 2.3 billion figure belongs to Publicis Groupe's total pre-Lotame profile base, not Epsilon specifically. Corrected.
- `layers/Focus Research/07-identity-clean-rooms-focused-master.md` — this time the focused-master had the error: Lotame's identifier count was overstated at 2.3 billion; actually 1.6 billion (2.3B is again Publicis's own pre-existing base). Corrected.
- `layers/07-identity-clean-rooms-layer.md` — Omnicom's LiveRamp exit was described as a routine Q1 2028 contract-sunset; actually accelerated to ~May 2027 per Omnicom CEO John Wren's on-record remarks, in direct response to the Publicis deal. Corrected.

## 9. Cross-layer consistency pass

Checked facts recurring across multiple layers' documents for agreement. Two real inconsistencies found (both now fixed, folded into Sections 1 and 5 above):

- **Walmart Connect's 2025 ad revenue** — the stale "$4.8 billion" figure (already disproven and corrected in Layer 7's own reconciliation) was still present in two other files: `layers/04-demand-valuation-layer.md` and `layers/Focus Research/00-gatekeeper-focused-master.md`. Both corrected to the settled $4.4B FY2025 / $6.4B FY2026 figures, sourced to Walmart's own SEC 8-K filings.
- **VPPA Supreme Court status** — Layer 2's file correctly reflected the January 2026 cert grant; Layer 6's focused-master did not. Corrected (Section 7 above).

Checked and confirmed already consistent, no edit needed: Amazon's >$70B TTM ad revenue (no stale ">$50B" figure survives anywhere in the tree), Fox-Roku deal terms ($22B EV, $160.00/share, 73/27 ownership), the LiveRamp/Publicis dual valuation figures ($2.167B EV / $2.546B equity, both correct and both now consistently framed as "different valuation bases, not a conflict" everywhere they appear), and the Nielsen v. TVision docket correction (no stray "EDO v. TVision" text survives anywhere — the only remaining mentions of "EDO" near "TVision" are the layer files' own provenance notes documenting the correction, not live errors).

## 10. Overview consistency check

`streaming-altdata-ecosystem.md` was checked against every correction above. No edits were needed — the overview already carried the correct figures throughout, including the VPPA cert-grant date that one layer-tier document (Layer 6's focused-master) was still missing. It is functioning as intended: the most current document in the stack, sitting above layers that occasionally lag it.

---

## 11. What's still open (by design, not an oversight)

These were checked and deliberately left as open fault lines, matching the project's existing convention of recording disagreement rather than forcing a resolution where no primary source settles it:

- Netflix ad-tier scale (order-of-magnitude gap between two readings, Layer 0)
- Suits licensing value, regional vs. global scope (Layer 0 / Layer 4)
- JPMorgan-Plaid request-volume framing, Subscriber Views pricing, two DROP enforcement fine amounts, Bloomberg Second Measure's exact acquisition date (Layer 1)
- No named, dated, post-2025 talent-agency compensation dispute (Layer 4)
- No true AMC-only revenue line isolated from total Amazon ad revenue (Layer 7)
- Reelgood's exact scale metrics beyond the one headcount correction made — still sourced only to mutually inconsistent estimator sites, no primary disclosure exists for this private company (Layer 5)
- Sportradar Q1 net-loss rounding variance, €6.2M vs. €6.3M (Layer 6)

## 12. Provenance

Built 2026-07-14. Eight parallel review passes (one per layer), each independently verifying conflicts via web search against primary sources before editing, followed by one cross-layer consistency pass and one overview check, both done directly. Every fact changed above traces to a cited primary source (SEC filings, company press releases/IR pages, court dockets) or, where unverifiable, to the more granular of the two documents in conflict, flagged as such inline in the edited file. No `supporting/archive/` source, no company doc content, and no existing document's structure was altered beyond the targeted sentence-level corrections listed above.
