# Layer 6: Sports-Rights Sub-Vertical (Master Findings)

> **Document type:** Master findings file (Deep Research integration), not a prompt file and not the diff map.
> **Created:** 2026-07-08, integration pass
> **Sources:** three Gemini Pro-tier passes. Filename numbering doesn't match creation order: the file named "Sports Rights Layer" (no suffix) was actually created first (02:34 UTC), "Sports Rights Layer 3" second (16:50 UTC), and "Sports Rights Layer 2" third and latest (16:51 UTC, one minute after "3"). Referred to below by creation order, Run A (earliest, unsuffixed), Run B ("3"), Run C ("2", latest), to keep the filename confusion out of this file.
> **Base document:** Run C, per `DEEP-RESEARCH-DIFF-MAP.md` Section 7
> **Readiness:** merged, one material fault line resolved via Reid-supplied primary source, one remaining discrepancy noted, all objectives closed or flagged

This is the densest prompt file of the eight (ten numbered objectives), several tied to local cross-references the research was explicitly told not to re-derive.

---

## 1. Findings by research objective

**1. Stats Perform/FIFA execution.** Run C alone answers the "issues/challenges" half: the xGOT model, the May 2026 FIFA Integrity Task Force (FBI, INTERPOL, UNODC, Sportradar, Genius Sports), no reported breaches as of research date. Runs A and B cover only deal terms.

**2. SIL/Zoomph, one year on.** Run A gives generic ROI stats. Run B names brands broadly (Legends, Kellanova, NASCAR, Monumental). Run C is the only pass naming specific late-2025 clients: the Washington Wizards, all 12 WNBA teams, and Ally Financial's 50/50 pledge. Run C is the strongest of the three on this objective.

**3. Streaming platforms' in-house data ambitions.** Run A is descriptive only. Runs B and C both explicitly frame the build-versus-buy question and converge on the same answer: platforms build in-house for ad targeting and personalization, but stay dependent on the triopoly (Sportradar, Genius, Stats Perform) for certified betting and integrity data. Run C adds a concrete Amazon-NBA illustration of that dependency in practice.

**4. Betting-handle correlation, named operator.** Runs A and C both cite the Sportradar-Kalshi deal (June 2026). Run B omits Kalshi entirely and gives an industry GGR revenue-share range instead. None of the three discloses actual dollar terms for a single deal.

**5. Competitive landscape and toll-layer verification.** Run C is most complete, naming rights holders and dates for UEFA, the Bundesliga, NASCAR, the NHL, MLB, and the NBA. Run B adds NCAA/CFP detail. Run A is thinnest.

**6. NHL, the CFP, and the Savannah Bananas.** Run A addresses none of the three. Run B is partial. Run C is decisive on all three, including the CFP's split between SportSource Analytics (the certified committee provider) and Genius's NCAA LiveStats.

**7. The journalism track.** Run A is silent. Run B is vague. Run C fully answers all three sub-asks, including a $60 million, three-year Barstool deal.

**8. ESPN Unlimited to MLB.tv/NBA League Pass.** Run A is silent. Run B offers only generic language. Run C gives a concrete mechanism (MyDisney account linking) and MLB.TV pricing, but no pass addresses NBA League Pass specifically. This remains open (see Gaps remaining).

**9. Sequencing conflict.** Run A is silent. Runs B and C both independently resolve to the same order. This is now a fully resolved fault line with a primary-sourced mechanism behind it (Section 4).

**10. Fox One pricing and Roku.** Run A is silent. Runs B and C conflict materially. Resolved (Section 4). Run C alone covers the Fox-Roku acquisition.

---

## 2. Corroborated across all or most variants

Stats Perform's January 2026 exclusive FIFA deal, covering the 48-team, 104-match 2026 World Cup, running an Opta plus RunningBall dual engine, including Bet LiveStreams. Sportradar's Q1 2026 financials (revenue roughly €346.5-347 million, up 11% year over year, adjusted EBITDA €66.0 million, a 19% margin). Genius Sports' Q1 2026 financials (Group Revenue $188.0 million, up 31% year over year, adjusted EBITDA $24.0 million). The SIL-Zoomph partnership, dated April 2025. Genius's acquisition of SIL, September 2025. Tickers: Genius (NYSE: GENI), Sportradar (Nasdaq: SRAD).

---

## 3. Additional detail pulled in from Run A and Run B (per the recommended integration approach)

Run C is the base; it leads or ties on nearly every objective. Two categories of material get pulled forward:

From Run A: the Paris 2024 Olympics cloud-infrastructure detail, deep NFL Next Gen Stats technical detail, Netflix Open Connect engineering detail, and the industry-wide GGR revenue-share range (12-25%).

From Run B: the taxonomy paragraph cross-referencing this layer into the framework's broader architecture (Layers 0, 1, 4, and 7), and the NCAA extension through 2032 with prop-bet ban detail. Run B's full regulatory-exposure section (Delete Act, CFPB 1033, VPPA, LiveRamp) is flagged here as likely belonging to the Identity/Clean Rooms or Wallet layer rather than Layer 6; it's noted rather than duplicated into this file, pending a scope call on where it should permanently live.

For objective 9 specifically, Reid's own sourced timeline document (dated 2026-07-07, thirty numbered citations to primary press and trade sources: ESPN.com, The Athletic, Deadline, Awful Announcing, Wikipedia) supplies the mechanism neither Gemini pass explains on its own. See Section 4.

---

## 4. Fault lines

**Resolved:**

Fox One's standalone price. Run B states $39.99, conflating standalone Fox One with the ESPN-bundled tier. Run C states $19.99 standalone, $39.99 only when bundled with ESPN Unlimited. Reid supplied a fox.com pricing-page screenshot confirming Run C's reading in full: Fox One Subscription $19.99/month or $199.99/year standalone, Fox One + Fox Nation bundle $24.99/month, ESPN Unlimited + Fox One bundle $39.99/month, B1G+ (Big Ten Plus) add-on $12.99/month or $89.99/year on any plan. Run B's flat $39.99 framing is confirmed wrong, the bundle price mistaken for the standalone price. Run C is the correct base for this objective; the Fox One + Fox Nation and B1G+ tiers are new detail beyond what any of the three passes surfaced independently.

Legend acquisition funding. This wasn't a clean Run A versus Run C conflict, both figures ("$850 million Term Loan B" and "$825 million term loan plus $220 million revolver plus $800 million cash plus 10.1 million shares") actually appear inside the same document (Run A), in two paragraphs that never reconcile with each other, most likely because Gemini pulled the $850 million figure from earlier deal-announcement coverage and the $825 million figure from later closing coverage without checking they described the same fact at two different points in time. Checked against the actual closing, Genius Sports' 6-K/credit-agreement disclosure (via SEC EDGAR, reported by Stock Titan and the Globe and Mail) confirms the final structure at close (April 30, 2026): $800 million cash plus 10 million-plus new shares as deal consideration, funded via a new credit agreement comprising an $825 million senior secured term loan (Term Loan A, not Term Loan B) at SOFR+350bps and a $220 million revolving facility, both maturing April 30, 2031. The $850 million Term Loan B figure was an earlier, superseded number from signing-stage coverage, not what actually closed. Use $825 million term loan / $220 million revolver / $800 million cash / 10 million-plus shares as the settled figures.

The sequencing conflict (objective 9). Two independent passes (Runs B and C) both found ESPN Unlimited launched August 2025, with the YouTube TV blackout following in November 2025, three months later, as a distributor reaction rather than the cause, against `espn-retention-analysis.md`'s earlier framing of the blackout as preceding and motivating the launch. Reid confirmed the Gemini reading directly and supplied a sourced timeline document (thirty numbered citations to primary press and trade sources) that supplies the mechanism the two passes only asserted without explaining: ESPN Unlimited launched August 21, 2025 without the leverage to dictate cable-carriage terms, then built that leverage afterward through the NFL's 10% ESPN equity stake plus the NFL Network/RedZone acquisition, the $325 million/year WWE rights deal, and a CW sublicensing pact for ACC/Mountain West/Pac-12 games. Every other major distributor (Charter Spectrum, DirecTV, Fubo, Cox) folded and granted authenticated app access to their pay-TV subscribers at no extra charge; Google didn't, which produced the two-week blackout. Resolution: YouTube TV agreed to fully integrate ESPN Unlimited into its base-plan subscriber UI (Deadline, November 2025). `espn-retention-analysis.md`'s sequencing was corrected 2026-07-07 to match this timeline (Section 5's Content Fortress Playbook steps re-ordered), that correction is now made, not just flagged.

**Open, recorded rather than resolved:**

NBA-Sportradar rights term. Runs A and C both find the deal runs through the 2030-31 season, not "through 2032" as the objective's own framing (borrowed from the Great Collision Substack post) assumed, suggesting a possible conflation with MLB's separate 2032 date. No pass flags this discrepancy itself; it only surfaces by checking the objective's framing against what the research actually found. Treat "through 2030-31" as the researched figure and flag the "2032" framing in the original prompt as likely a cross-reference error, pending a check against the original Substack post.

**Minor, not elevated to fault-line status:** Sportradar's Q1 figures vary trivially between Run A (€347M/€6M/€9M) and Runs B/C (€346.5M/€6.3M/€9.3M), rounding only.

---

## 5. Gaps remaining

No pass addresses the NBA League Pass connection mechanism; only MLB.tv is covered under objective 8.

No pass discloses actual dollar-value commercial terms for a single sportsbook data deal.

The "400+ leagues" aggregate claim from the toll-layer thesis is never tallied or independently verified by any pass.

Objective 9's ask for another rights holder running a comparable playbook is answered only generically (WBD, PSKY named) without a dated, concrete parallel case.

`espn-retention-analysis.md`'s launch/blackout sequencing was corrected 2026-07-07; that correction is complete, not a remaining gap, noted here only so this file's own record matches the current state of that file.

---

## 6. Provenance

Synthesized from `DEEP-RESEARCH-DIFF-MAP.md` Section 7 (three Gemini Pro-tier passes, 2026-07-07). Two fault lines resolved using primary sources already logged in the diff map (fox.com pricing page via Reid, SEC EDGAR/Stock Titan/Globe and Mail for the Legend Term Loan A structure, Reid's own thirty-citation sourced timeline for the sequencing objective). No new research performed in this integration pass. Fault-line convention follows `streaming-altdata-ecosystem.md` Section 6.
