# Deep Research Diff Map: Streaming Alt-Data Ecosystem

> **Document type:** Consolidation guide, not a research file. Records what the 17 Gemini Deep Research passes across the 8 layer prompts agree on, where they conflict, and how each layer's variants should be merged into one master findings file per layer.
> **Created:** 2026-07-07
> **Last updated:** 2026-07-08, folding in three additional Deep Research passes for Layers 2, 3, and 5 (see the note at the end of Section 10).
> **Status:** Working reference for a future integration pass. No source docx or layer prompt files were edited to produce this. No new research content was generated, every fact below traces to one of the Deep Research outputs already sitting in `supporting/` or, for the three added 2026-07-08, uploaded and still awaiting archival (see Section 10).
> **Sources reviewed:** the original 17 docx files in `supporting/`, plus 3 additional MD passes added 2026-07-08 (Layer 2 Glass second Pro pass, Layer 3 Shield second Pro pass, Layer 5 Funnel Flash pass, uploaded as 4 files, two of which are a byte-identical duplicate of the same Glass Layer pass), all cross-checked against the corresponding `layers/00-gatekeeper-layer.md` through `layers/07-identity-clean-rooms-layer.md` numbered research objectives, which served as the grading rubric for each pass.

---

## 0. How to read this

Each of the 8 sections below covers one layer and follows a fixed structure: objective coverage (scored against that layer's prompt file), what's corroborated across variants, what's unique to one variant, conflicts recorded as fault lines (per the convention already established in `streaming-altdata-ecosystem.md` Section 6, disagreements get stated plainly rather than silently resolved), a recommended base document plus what to pull in from the others, and what's still missing after all passes.

**Target format for the actual `layers/*.md` master files, added 2026-07-09 after the first integration attempt missed this.** This diff map's own structure (objective-by-objective breakdown, an explicit "Fault lines: Resolved/Open" section, a "Gaps remaining" bullet list, "Provenance" citing docx filenames) is an internal working format, useful here, wrong for the master files themselves. The master files should read as institutional white papers in the same voice as the 20 source documents in `supporting/`, executive summary or orientation framing, thematic prose sections with real narrative headers, resolved conflicts folded into the prose as settled fact with an inline citation rather than surfaced in a separate audit-style section, and open conflicts stated plainly within the relevant paragraph (matching `streaming-altdata-ecosystem.md` Section 6's own convention) rather than quarantined into a "Fault lines" appendix. A brief provenance note is fine at the end, a full merge-authority/sources/readiness metadata block at the top is not, that reads like a workpaper header, not a research document's front matter. This is a voice and structure fix, not a content fix, everything factual in the current `layers/*.md` files (fault-line resolutions, preserved gaps, preserved open conflicts) is correct and should carry over, just reformatted into that voice.

**Summary table:**

| Layer | Variants run | Model tiers | Recommended base | Readiness |
|---|---|---|---|---|
| 0: Gatekeeper | 3 | Pro x3 | Run 3 (latest, 17:50 UTC) | Needs merge, has fault lines |
| 1: Wallet | 4 | Pro, Finance, Flash, FlashLite | Pro | Needs merge, has fault lines |
| 2: Glass | 2 (added 2026-07-08) | Pro x2 | Run 2 (2026-07-08 pass), strict superset of Run 1 plus one correction | Ready to merge, one fault line resolved, no open conflicts |
| 3: Shield | 2 (added 2026-07-08) | Pro x2 | Run 2 (2026-07-08 pass), strict superset of Run 1 | Ready to merge, no fault lines |
| 4: Demand/Valuation | 2 | Pro, FlashLite | FlashLite | Needs merge, has fault lines |
| 5: Funnel | 2 (added 2026-07-08) | Pro, Flash | Merge both, genuinely additive, not a base-plus-pull situation | Ready to merge, no fault lines, delivered fully contrary to the "thin" risk flagged in the prompt |
| 6: Sports-Rights | 3 | Pro x3 | Run "3" (per filename, actually the second-created of the two later runs) | Needs merge, has a material fault line on Fox One pricing and the ESPN Unlimited/blackout sequencing |
| 7: Identity/Clean Rooms | 2 | Unlabeled x2 | Run 02 | Needs merge, has fault lines, both variants share one gap (neither re-confirmed deal status as of the actual review date) |

---

## 1. Layer 0: Ecosystem Gatekeepers

Three independent Pro-tier passes, run within about 45 minutes of each other on 2026-07-07 (17:06, 17:48, 17:50 UTC).

**Objective coverage**
1. Amazon dual posture: strong in Runs 2 and 3 (hard TTM ad figures, AMC mechanics, named studio complaints). Run 1 covers it directionally but understates the ad-revenue figure and gives an unsourced paraphrase of the studio complaint.
2. Apple posture resolved: strongest in Run 2 (on-record, dated Eddy Cue quote, Nov 2025). Run 3 close second with fuller financial detail. Run 1 states the conclusion with no primary-source citation.
3. Roku centrality: all three quantify it, on different cuts. Run 3 uses FY2025 annual figures split three ways (Advertising/Subscriptions/Devices). Run 2 uses Q1 2026 quarterly figures split two ways (ex-Devices). Run 1 gives a single TTM headline number. Same growth story, three different snapshots.
4. Netflix exception closing: all three address it and track the same $3B 2026 ad-revenue target, but disagree sharply on ad-tier scale (see fault lines).
5. Layer-by-layer flow mapping: Run 1 is one line per layer, the weakest treatment. Runs 2 and 3 both run full per-layer sections; Run 3 adds Shield-layer fraud-rate data and Sports-Rights toll-layer detail, Run 2 adds the NBA rights-settlement narrative under Demand/Valuation and Sports-Rights.
6. PSKY/WBD stress-test plus Fox-Roku tie-in: all three converge on reclassifying Paramount Skydance/WBD as vendor subject, not gatekeeper, and match on Fox-Roku deal mechanics. Run 2 has the fullest NBA settlement account.
7. Relative centrality of the 8 gatekeepers: all three converge on the same ranking (Roku/Fox/Disney structurally central, Amazon/Apple/Google side effects of larger businesses, Paramount Skydance/WBD a distressed subject).

**Corroborated across all/most variants**
Fox-Roku deal terms match exactly across Runs 2 and 3: $22B enterprise value, June 15 2026, $160/share ($96 cash plus 0.9693 FOX shares), $12B Morgan Stanley bridge, roughly 73/27 Fox/Roku post-close ownership, $400M run-rate synergies, 2.8x pro forma leverage, close targeted H1 2027. All three agree Apple runs no clean room, Apple TV+ is pure ecosystem bait blended into Services. All three match on Paramount Skydance's WBD acquisition (Feb 27 2026, $110.9B, $31/share cash, outbid Netflix). All three cite the Nov 2025 Google/Disney YouTube TV blackout at roughly $110M cost to ESPN, roughly 8M YouTube TV subscribers.

**Unique to one variant only**
- Run 1: Disney's "Fubo acquisition response" as part of its bundling defense, not developed elsewhere.
- Run 2: WGA National Labor Relations Board unfair-labor-practice charge against Amazon over withheld Prime Video data (a stronger, more current complaint citation than the other two); full NBA rights-settlement account (WBD loses US rights to Disney/Amazon/NBCUniversal, keeps international plus Bleacher Report, Inside the NBA moves to ESPN); Q1 2026 Amazon-Audiences-on-Netflix integration; LiveRamp/Publicis at $2.54B.
- Run 3: CTV bot fraud up 140% year over year (Shield layer); Genius Sports' NFL exclusivity through 2029 (Sports-Rights layer); NBCUniversal withholding the final Suits season from Netflix to drive a Peacock "halo effect" (Demand/Valuation layer); Amazon's Forrester TEI study (240% ROI, 65% reduced waste); LiveRamp/Publicis at $2.16B.

**Conflicts / fault lines**
- Netflix ad-tier scale: Run 3 states surpassing 40 million global users by 2025; Run 2 states 250 million MAU by the May 2026 upfronts (up from 190 million late 2025). Order-of-magnitude gap, both cited to the same window.
- **LiveRamp/Publicis price, resolved 2026-07-07, not actually a conflict.** Verified directly against Publicis Groupe's own press release (publicisgroupe.com, dated 2026-05-17): total enterprise value $2.167 billion, acquisition price $38.50/share, total equity value $2.546 billion, acquired net cash $379 million ($2.546B equity value minus $379M net cash = $2.167B EV, the arithmetic ties out exactly). Run 2's "$2.54B" is the equity value, Run 3's "$2.16B" is the enterprise value, both are correct, they were just measuring two different things and neither variant labeled which one it was quoting. Use $2.167B EV / $2.546B equity value as the settled figures going forward, matching the main map's Section 4.
- **AMC lookback-window expansion, resolved 2026-07-07, not actually a conflict.** Run 2 says 13 months extended to 5 years (early 2025); Run 3 says 13 months extended to 25 months (mid-2026). These looked like a direct conflict on the same event, but the Layer 7 Identity/Clean Rooms review (variant "02") spells out that Amazon did two separate, non-conflicting things: extended the *ad-traffic* lookback window from 13 to 25 months (following its unBoxed 2025 event, matching Run 3), and separately unlocked up to 5 years of *historical data for store-purchase signals and video viewership* (matching Run 2). Run 2's half is backed by a real primary source already in its own works-cited list: Amazon's own advertising.amazon.com blog post announcing the 5-year retail lookback. Both figures are correct, they describe two different datasets within AMC, not one contested figure.
- **Amazon TTM ad revenue, resolved 2026-07-07.** Verified directly against Amazon's own Q1 2026 earnings release (aboutamazon.com, reported April 29, 2026, for the quarter ended March 31, 2026): Andy Jassy's own quote states "Advertising grew to over $70 billion in TTM revenue," with Q1 2026 advertising services revenue of $17.24B (+24% YoY, per the earnings coverage). Runs 2 and 3's "$70 billion TTM by Q1 2026" is correct and current. Run 1's ">$50 billion annually" is stale, it undercounts the actual figure by roughly $20 billion. This same conflict recurs in the Layer 7 review below, resolved the same way, once, not twice.
- Roku/Tubi FAST viewing share: Run 2 says the Roku Channel alone holds 6.3% of US streaming time (number two behind YouTube); Run 3 says Tubi plus Roku Channel combined, pre-merger, hold 5.2% (Nielsen Gauge). A combined figure should exceed the single-app figure for the same period; as stated they don't reconcile.
- Suits licensing value: Run 2 says $356M in US/Canada subscriber revenue; Run 3 says "over $800 million in global licensing value." Different scope (regional vs. global), each presented as a standalone headline figure. (Matches the two figures already sitting side by side, unreconciled, in the main map's Section 4.)

**Recommended integration approach**
Use Run 3 (latest, 17:50 UTC) as the base. It carries the most rigorous primary-sourced financials (10-K-level segment detail for Amazon, Apple, Roku), the fullest Shield and Sports-Rights layer development, and its own works-cited list. Pull into it from Run 2: the WGA NLRB filing (a stronger objective-1 complaint citation than Run 3's older FTC letter), the full NBA rights-settlement paragraph (needed for objective 5/6 Sports-Rights coverage), and the Netflix/Amazon Audiences cross-platform note. Pull nothing load-bearing from Run 1, it is a thinner subset of the other two with an apparently stale Amazon ad-revenue figure, keep only as a directional cross-check.

**Gaps remaining**
None of the three runs delivers a true bidirectional flow map, all describe what gatekeepers withhold that creates vendor demand, but rarely what flows back from vendor layers to gatekeepers. No variant isolates Roku Data Cloud/OneView revenue specifically, it stays bundled inside Platform/Advertising.

---

## 2. Layer 1: Wallet (Subscriber Transaction Intelligence)

Four passes across four model tiers: Pro (2026-07-06, earliest), Finance, Flash, FlashLite (all three 2026-07-07 midday, roughly 90 seconds to 2 minutes apart).

**Objective coverage**
1. Ownership/capital structure: all four cover it well. Pro and Flash agree YipitData has not filed an S-1 (still "preparation phase"). Finance uniquely claims a confidential S-1 has been submitted, direct conflict (see below). FlashLite adds the most current fact of the four: Henry Schuck (ZoomInfo CEO) joined YipitData's board April 13, 2026.
2. Margin compression/Plaid precedent: all four cover the JPMorgan-Plaid deal solidly. None confirm BofA/Wells/Citi have activated identical fees. FlashLite goes furthest (PNC executives Demchak and Overstrom endorsing the model, directing clients to Akoya); Flash adds BofA's early-2026 API migration timeline.
3. DROP compliance: all four correctly note the Aug 1, 2026 deadline hasn't passed, no Wallet-layer vendor cited for a deletion failure. Flash and FlashLite go further, citing real CPPA registration-failure fines against non-Wallet-layer brokers (S&P Global, Rickenbacher/Datamasters, Jerico Pictures) as evidence enforcement infrastructure is active.
4. Subscriber Views depth: none confirm public pricing or a named client roster. Flash and FlashLite each supply pricing estimates that disagree with each other (see fault lines). Flash's CLTV case study ($186.71 vs $122.48) is the most granular data point on the product across all four.
5. Consumer Edge/Earnest fusion: all four converge, partial integration, not a fused product. Flash gives the best mechanistic explanation (HIPAA de-identification, schema incompatibility). FlashLite complicates the "still siloed" conclusion with a June 2026 combined forecasting report.
6. New entrants/exits: weakest objective across all four. None finds a new zero-party entrant disrupting the incumbent hierarchy. Flash is the only variant naming actual exit/M&A events (though outside strict Wallet-layer scope).

**Corroborated across all/most variants**
YipitData: Carlyle $475M Series E (Dec 2021), Norwest $175M (2019), CIBC debt facility (June 2024), 60-75% institutional voting power, 1010data acquisition (2023). Consumer Edge acquired Earnest Analytics April 2025 (Orion/Vela, Phoenix Pharmacy Claims, Leo Medical Claims). Antenna: BDMI/Raine/Foundry Group backing, "Subscriber Views" fuses ACR with transaction panels, Stick drove roughly 33%/700k Apple TV+ signups June 2025, Buccaneers 98% vs 92% retention. JPMorgan-Plaid: roughly $300M potential annual fee estimate (Forbes), "fractions of a cent per pull," Plaid absorbing costs for now. CFPB 1033 blocked by Judge Danny Reeves, Oct 2025. DROP: $200/day/violation, 45-day query cycle, Aug 1, 2026 trigger, over 215,000 CA registrants by mid-2026 (Finance and Flash agree).

**Unique to one variant only**
- Pro: cross-layer triangulation methodology detail, "serial churner" $9B market sizing, AI-native disruption thesis (Gemini/Google Pay, OpenAI agentic shopping as long-term Wallet-layer threat).
- Finance: CoVenture $60M funding for Consumer Edge (Jan 2023), Earnest founder Kevin Carson (2012), "Basketview Signal CPG" product name, zero-party platform comparison table (Fetch 17M+, Ibotta 40M+, Rakuten, Shopkick, Receipt Hog with user counts), bank stock price table.
- Flash: Subscriber Views "unveiled October 2025" (unconfirmed elsewhere), RRE Ventures $6M Series A (2011), statistical variance formula for panel degradation, named M&A exits (Novacap/IAS $1.9B, Mediaocean/Innovid, Comscore/Advaya $70M, Ampere/PlumResearch).
- FlashLite: Henry Schuck board appointment (Apr 13, 2026), YipitData/ANSR India GCC partnership, PNC named executives, ESPN Unlimited/Fox One as Subscriber Views sports adopters, compliance cost estimate ($150k-$350k/year), Jerico Pictures fine.

**Conflicts / fault lines**
- **YipitData IPO status, resolved 2026-07-07 by sourcing quality, not by an external check.** Pro and Flash say no S-1 filed, still in preparation. Finance says a confidential S-1 has been submitted, IPO "stalled" pending market conditions. Checking each claim's own citation: Pro and Flash both trace their "no S-1" reading to aggregator/marketplace profiles (PitchBook, Built In, EquityZen) that are at least the right *kind* of source for a company-status claim. Finance's "confidential S-1 submitted" claim traces to a single citation, a Hiive pre-IPO share-price listing page, which is a private secondary marketplace with no visibility into confidential SEC filings and no plausible way of actually knowing that. That citation cannot support the claim it's attached to. Weight of evidence and citation quality both favor "no S-1 filed as of each variant's research date," treat Finance's claim as unreliable rather than as a genuine competing data point. Note this is a within-document-citation check, not a fresh external verification, worth a real SEC EDGAR confidential-draft disclosure check if the IPO timing becomes decision-relevant later.
- JPMorgan request volume: Pro cites 1.89 billion requests in June 2025 specifically. Finance cites "approximately two billion account access requests monthly, up from one billion in 2023," a different framing and base period.
- Subscriber Views pricing: Flash says "mid-six-to-seven-figure" annual commitments. FlashLite says "low-to-mid six figures." Materially different magnitude claims for an undisclosed figure, neither sourced to a named client contract.
- DROP enforcement fine amounts: Flash says Rickenbacher fined $42,000, S&P Global $62,000. FlashLite says Rickenbacher $45,000, S&P Global $62,600. Same two enforcement actions, different dollar figures.
- Bloomberg Second Measure acquisition date: Finance/Flash say "late 2020." FlashLite specifies December 24, 2020, and separately flags what looks like a database error conflating a re-parsed 2019 Series A with a phantom "2026 Series A."

**Model-tier quality read**
Pro is not clearly superior. Its prose synthesis and methodological framing (cross-layer triangulation, the AI-disruption thesis) are the most sophisticated of the four, but it is thinner on hard, checkable facts than Flash and FlashLite, no DROP enforcement examples, no named M&A exits, no board-appointment news. Flash surfaced the most concrete new data points overall. FlashLite surfaced the single most current, verifiable fact in the set (Schuck's board seat). Finance's sourcing is notably weaker, only 3 works cited versus 26-34 in the other three, despite its confident-sounding tables. Running FlashLite alongside Pro looks like better ROI than running Finance going forward.

**Recommended integration approach**
Use Pro as the base, its structure and prose match the framework's expected register and its 26-source bibliography is solid. Pull in from FlashLite: the Schuck board appointment, the ANSR India GCC detail, and the DROP enforcement examples (flagging both dollar-figure readings as unresolved). From Flash: the HIPAA/Datavant explanation for the Consumer Edge/Earnest fusion gap, the CLTV case study, and the named M&A exit list (labeled adjacent-layer, not strict Wallet-layer). From Finance: the zero-party platform table and the CoVenture funding detail for Consumer Edge. Record the S-1 status conflict and the Subscriber Views pricing conflict as open fault lines rather than resolving them.

**Gaps remaining**
No variant produced a confirmed dollar figure any Wallet-layer vendor (not Plaid) is actually paying banks. No variant named a specific, confirmed Subscriber Views client. No variant confirmed or denied BofA/Wells/Citi per-pull fees with a primary source, only directional commentary. No variant identified a genuinely new zero-party entrant disrupting the incumbent hierarchy since mid-2026.

---

## 3. Layer 2: Glass (Hardware / ACR)

Two Pro-tier passes now. Run 2 (added 2026-07-08, uploaded as two byte-identical files, "Glass Layer Research Brief Execution.md" and "02 - Deep Research - Pro v2 - Glass Layer.md", confirmed identical by checksum, treat as one document) substantially deepens Run 1 rather than just re-confirming it, and corrects one real error.

**Objective coverage**
1. Nielsen fault line: resolved in Run 1 already, fully corroborated by Run 2 on every date and figure (MRC accreditation timeline, the March 3, 2026 marketplace update, the May 27, 2026 delay to August 31, 2026, the VAB Gauge suppression dispute). Run 2 adds one fact Run 1 didn't have: Nielsen's separate Audio Diary service went on a six-month MRC accreditation hiatus, June 23 through December 23, 2026.
2. VideoAmp/iSpot upfront share: substantially deepened by Run 2 with dated figures Run 1 lacked entirely, VideoAmp's trajectory from ~$3B (2024) to a projected ~$6B (2026), and iSpot's $128M 2025 revenue (+22% YoY) plus its influence over an estimated $18B-$22B of upfront spend across NBCUniversal, Paramount, and AMC Networks. Run 2 also covers Comscore's regulatory standing (fully JIC certified, MRC-accredited for Local TV Demographics since April 2025), which Run 1 never addressed.
3. Samba TV / Inscape: corroborated on the Project Gravity launch (Run 1 dated it May 26, 2026; Run 2's own press-release citation dates it May 21, 2026, both inside the same week, treat as the same event). Run 2 adds ownership detail (August Capital, Union Grove, plus equity stakes held by Disney, IPG, and Warner Bros. Discovery, ~$750M valuation estimate) and two named acquisitions (Semasio, October 2024; Bestever AI, June 2026). Run 2 also reframes Inscape's post-Walmart status: not just arm's-length licensing routed through iSpot, but a dual-track strategy that keeps external licensing to VideoAmp and iSpot running alongside deep internal integration into Walmart Connect's closed-loop attribution (2026 IAB NewFronts joint presentation, a named L'Oréal shoppable-content pilot, a unified login rolled out across Vizio OS and "onn" TVs), a fuller picture than Run 1's framing.
4. EDO v. TVision: **real fault line, resolved 2026-07-08 via independent primary-source check.** Run 1 named the litigants as EDO Inc. v. TVision on Delaware docket 1:2025cv00575. Run 2 states the real litigants are Nielsen v. TVision, on that same docket, five separate patent suits filed since 2021, a November 10, 2025 antitrust counterclaim from TVision, and a June 2026 jury verdict of non-infringement in TVision's favor. Checked directly against CourtListener (docket 1:25-cv-00575, "Nielsen Company (US), LLC v. TVision Insights, Inc.") and Cohen Milstein's own case-study page: Run 2 is correct, Run 1 had the right docket number but the wrong plaintiff. Separately, and also new in Run 2: Viant Technology agreed to acquire TVision Insights for $40M ($22.5M cash, $17.5M stock), independently confirmed via Viant's own April 15, 2026 8-K and press release, expected to close in Q2 2026 (Run 2's stated "early May 2026" close is inside that window). Run 1's "no acquisition or materially expanded footprint for either party as of mid-2026" isn't wrong for its research date, just superseded by an event roughly two and a half months later.
5. Holding-company multi-currency commitment: **the objective Run 1 flagged as its weakest is substantially answered by Run 2.** GroupM (WPP) is named as having formally designated VideoAmp a preferred currency for a significant share of its national commitments; Omnicom Media Group, IPG Mediabrands, Publicis Media, and Dentsu are named as having deeply integrated both VideoAmp and iSpot into 2027-upfront planning, bidding, and reconciliation workflows, with agency guidance treating a "Nielsen-only" publisher posture as a structural pricing disadvantage. This is the named, dated commitment Run 1 said didn't exist yet.

**Corroborated across both variants**
Nielsen's National Big Data + Panel accreditation and audit timeline in full; the VAB Gauge suppression dispute and its March 19, 2026 WSJ-leak figures (linear 47.4% vs. streaming 41.9%); Samba TV's Project Gravity launch.

**Unique to one variant only**
- Run 1 only: nothing that survives, its two distinguishing claims (EDO v. TVision, Inscape as purely arm's-length) are both superseded above.
- Run 2 only: the full VPPA circuit-split legal section (the Second Circuit's broad *Salazar v. NBA* reading vs. the Sixth Circuit's narrower *Paramount* "consumer" definition, up to $2,500-per-violation liquidated damages exposure, the Sony/Vizio historical class-action record), which Run 1 never addressed despite it bearing directly on this layer's core legal exposure; Samba TV's ownership and acquisition detail; Comscore's regulatory status; the Viant/TVision deal.

**Conflicts / fault lines**
EDO v. TVision, resolved above, the only real conflict this layer produced. Everything else is Run 2 either corroborating or adding to Run 1 with no contradiction.

**Recommended integration approach**
Use Run 2 as the base, it corrects Run 1's one factual error, closes Run 1's own flagged weakest objective, and adds the VPPA section Run 1 lacked entirely. Nothing needs pulling forward from Run 1 specifically, Run 2 is a near-strict superset once the EDO/Nielsen correction is applied.

**Gaps remaining**
Objective 2's "confirmed actual, not projected" 2026 upfront dollar results still isn't fully closed, VideoAmp's ~$6B figure remains explicitly a projection in Run 2 too. No named 2027 holdco commitment yet for iSpot specifically, only for VideoAmp (via GroupM).

---

## 4. Layer 3: Shield (Media Quality Verification / Fraud)

Two Pro-tier passes now. Run 2 (added 2026-07-08, uploaded as "Shield Layer Research Brief.md") corroborates every figure in Run 1 with no fault lines, and substantially closes both objectives Run 1 flagged as weak.

**Objective coverage**
1. IAS post-privatization: corroborated in full on deal mechanics ($1.9B EV, $10.30/share, 22% premium, closed Dec 23, 2025, Novacap's TMT VI fund, Jefferies/Evercore advisors, Vista Equity Partners' full exit). Run 2 adds one major fact Run 1 didn't have: Lidiane Jones (ex-CEO Bumble, ex-CEO Slack under Salesforce, prior product leadership at Microsoft and Sonos) was named CEO of IAS effective July 7, 2026, succeeding Lisa Utzschneider, who moves to Special Advisor through end of 2026. Given Run 1's research date, this most likely postdates it rather than contradicts it.
2. DV FY2026 guidance: fully corroborated ($180.8M Q1 2026 revenue, +10% YoY, 31% Adj EBITDA margin, -$6.4M FCF, FY26 guidance of $810M-$826M). Run 2 adds segment-level detail Run 1 lacked: Activation revenue $100.5M (+6%), Measurement $61.8M (+16%), Supply-Side $18.5M (+12%), Social Measurement +23%, Social Activation +92%, the underlying volume-vs-pricing dynamic (Media Transactions Measured +12%, Measured Transaction Fees -4%), $173.8M cash with zero debt, and $100.2M in share buybacks year-to-date.
3. New entrants/disintermediation: **the objective Run 1 flagged as needing a follow-up (its HDFC Bank hyperscaler example was a weak analogical stretch) is substantially strengthened by Run 2.** Run 2 corroborates the Scope3-to-Peer39 Adloox chain with more precision (Adloox acquired November 4, 2024; Scope3's "Agentic Media Platform" launched March 2026 with Amazon DSP integration and Scope3's own quote, "Scope3 is not an ad verification company"; Adloox divested to Peer39 June 2, 2026; Peer39's resulting access spans Google DV360, integrated since 2014, and Meta, since February 2024) and drops the bank analogy for a structural argument instead, naming The Trade Desk's Koa/Kokai bidding algorithms and Google/Meta's native brand-safety centers as the actual tools in question and arguing DSPs won't fully disintermediate independent verifiers because they can't credibly grade their own inventory. The narrow ask, one concrete named hyperscaler in-house deployment, still isn't answered by either variant, but the objective's real substance now is.
4. AI fraud sophistication: fully corroborated (140% YoY CTV fraud surge from DoubleVerify's May 2026 "Must-CTV" report, $1.8M-per-billion-impression fraud cost, and a regional split, NA 82% bot fraud vs. APAC 98% / LatAm 91% / EMEA 66% data-center fraud, that matches Run 1 almost verbatim). Run 2 adds a major named case study Run 1 lacked entirely: HUMAN Security's Satori team disrupting "NewsJunkie," a July 2026 SSAI device-spoofing operation pairing forged device metadata with residential-IP laundering, at its peak generating hundreds of millions to nearly two billion invalid CTV bid requests per day. Also new: DoubleVerify's own named AI countermeasure products, "DV Neura" (claimed 300x classification speed) and "DV AI SlopStopper."
5. Advertiser adoption gap: **the objective Run 1 flagged as weakest (a stale 2023 ANA citation) is substantially closed by Run 2.** Run 2 cites an ANA Programmatic Media Supply Chain report "updated through 2025," quantifying global unrealized media value at $26.8B in 2025, up 34% from $20B in 2023, plus supporting figures (44,000 average websites per campaign, 21% of impressions and 15% of spend going to Made-for-Advertising sites). The "fewer than 21%" KPI-adoption figure itself is unchanged between variants, but Run 2 now grounds the broader waste argument in a dated 2025 figure Run 1 didn't have.

**Corroborated across both variants**
IAS deal terms in full; DoubleVerify's Q1 2026 headline financials in full; the 140% CTV fraud surge and its regional bot-vs-data-center split; the Scope3-to-Peer39 Adloox chain; the "fewer than 21%" advertiser-adoption KPI figure.

**Unique to one variant only**
- Run 1 only: nothing substantive that Run 2 doesn't also cover or supersede.
- Run 2 only: Lidiane Jones's CEO appointment; DV's segment-level revenue breakdown and buyback detail; the NewsJunkie case study; the DV Neura and SlopStopper product names; the 2025-updated ANA waste figure; the structural (rather than analogical) disintermediation argument.

**Conflicts / fault lines**
None found. Run 2 corroborates Run 1 on every shared figure and adds new material without contradicting it.

**Recommended integration approach**
Use Run 2 as the base, there are no fault lines to reconcile and it strictly deepens Run 1 on every objective, including both of Run 1's own flagged weak spots. Nothing needs pulling forward from Run 1 specifically.

**Gaps remaining**
The narrow version of objective 3, one concrete named hyperscaler in-house fraud-detection deployment rather than a bank analogy or a structural argument, is still technically open. No survey specifically fresher than the prompt's own premise on the 21% KPI-adoption figure itself, only on the dollar-waste figure surrounding it.

---

## 5. Layer 4: Demand/Valuation (Audience Demand & IP Valuation)

Two passes: FlashLite (2026-07-06 23:45 UTC, earlier) and Pro (2026-07-07 02:05 UTC).

**Objective coverage**
1. Ampere/PlumResearch: both cover the May 26, 2026 acquisition and June 16, 2026 NIQ Japan Showlabs launch. FlashLite stronger (AIM Rule 15 mechanics, June 8 shareholder vote at 44.3% approval, close date June 10, named execs retained).
2. Parrot's next case study: FlashLite clearly stronger, supplying multiple dated post-mid-2026 studies (Spanish-language content June 2026, Japanese anime June 24 2026, Eternaut Jan 15 2026) with dollar figures. Pro stops at a mid-2025 comparison and an undated case.
3. Gracenote posture: both confirm metadata-only. FlashLite materially deeper, including an April 8, 2026 Gracenote chatbot-discovery report that Pro never connects to Gracenote.
4. Whip Media/TV Time/Luminate: both cover the Blue Torch acquisition and July 15, 2026 TV Time shutdown. FlashLite adds executive names and Luminate scale detail (conflicting with Pro, see below).
5. Talent-agency concrete deal: neither variant fully answers this. Pro stays general (no named dispute). FlashLite cites Tommy Lee Jones v. William Morris Agency (DLSE TAC 16396, $15M claim) but flags it as historical precedent, not post-2025.
6. Foundation-model-native entrants: complementary, not overlapping. Pro covers Previsible and Profound; FlashLite covers Diesel Labs (PanelAI, Daisy) and IQRush. Combined, well answered, neither alone is complete.

**Corroborated across both variants**
Ampere-PlumResearch deal structure and May 26, 2026 date; Suits/Netflix $356M UCAN (Q1 2020-Q4 2024, $800M+ global); reality-competition case (144% demand lift, $120M+/season); 2025 streaming churn figure of $6.3 billion; Whip Media's Blue Torch acquisition (Feb 2025), $11.4M ARR, roughly 104 employees; TV Time shutdown July 15, 2026; Gracenote's 14-minute average search time and 19%/29% session-abandonment rates.

**Unique to one variant only**
- Pro only: WWE-Netflix $5B/10-year deal retaining 1.25M subs/quarter; NFL shoulder-content retention (500K subs); Previsible/Profound GEO vendors; agentic-commerce protocols (MCP, UCP, AP2).
- FlashLite only: Gilded Age ($70M, June 29, 2025), Spanish-language ($5.1B/4yr), Japanese anime ($21.9B, $2.7B Netflix share), Eternaut ($34M Argentine economic impact); Diesel Labs/IQRush; Gracenote's April 2026 chatbot-discovery study; Whip Media leadership roster; Luminate's $100M-$250M revenue and 1,400 institutional clients.

**Conflicts / fault lines**
- **Luminate headcount, resolved 2026-07-08.** Pro states roughly 187 employees; FlashLite states 750-860 plus $100M-$250M revenue. Checked against three independent company-intelligence databases (PitchBook, GetLatka, Built In, all confirmed via direct WebSearch against pitchbook.com's own Luminate Data profile and cross-referenced by Reid's own check), all three converge on 187 employees (LeadIQ separately estimates ~193 as of June 2026, consistent within normal estimate variance). Actual revenue is reported around $7.5 million ARR, not $100M-$250M. Pro is correct, FlashLite's 750-860 headcount and $100M-$250M revenue figures do not match any database and most likely got pulled from an unrelated entity during generation. Use Pro's 187-employee figure in the integrated layer file, drop FlashLite's headcount and revenue claims entirely rather than presenting them as a range.
- Luminate data points: "30 trillion" (Pro) vs. "23 to 30 trillion" (FlashLite).
- Whip Media capital raised: $115M (Pro) vs. $115.5M (FlashLite).
- Showlabs commercial positioning: Pro frames the NIQ launch as Japan-specific standalone; FlashLite frames it as bundled regional subscriptions across seven markets. Different characterizations of the same rollout.
- PlumResearch early backers: Pro names only Tar Heel Capital Pathfinder; FlashLite adds Montis Capital and PFR Ventures.
- Reality-competition case study dating: Pro leaves it undated ("post-2025"); FlashLite dates it finalized March 30, 2025, published July 17, 2025, which itself is pre-mid-2026 and doesn't fully satisfy the objective's "since mid-2026" ask.

**Model-tier quality read**
FlashLite is surprisingly competitive and in places stronger, especially on dated, sourced case studies and deal mechanics. Pro reads more narratively and covers the LLM-disruption thesis with more analytical framing. Neither is uniformly superior, FlashLite has more granular facts, Pro has more synthesis.

**Recommended integration approach**
Use FlashLite as the factual base for M&A mechanics, case-study currency, and Gracenote's AI-discovery pivot. Pull from Pro: the WWE/NFL churn-retention figures, the Previsible/Profound GEO vendor coverage, and the agentic-commerce framing.

**Gaps remaining**
Objective 5 (a specific, named, post-2025 talent-agency deal tied to a compensation outcome) is unmet by both, the only named dispute predates the window. Flag for a targeted follow-up query.

---

## 6. Layer 5: Funnel (Downstream Intent & Discovery)

Two passes now, Pro (original) and Flash (added 2026-07-08, uploaded as "05 - Deep Research - Flash - Funnel Layer.md"). The prompt file flagged this layer as most likely to come back thin, neither pass did, and Flash held up well against Pro, consistent with this review's recurring finding that cheaper Gemini tiers are surprisingly competitive.

**Objective coverage**
1. Ownership/scale from scratch: both deliver on all three vendors, matching within normal estimate variance. JustWatch: Pro's ~$68M 2026 estimate sits inside Flash's $50M-$100M range; Pro's 200-243 employees matches Flash's "exceeding 200" (Flash adds the growth curve, 56 employees in 2020 to 200+ by 2026, across eight offices and 46 nationalities, plus 50M+ monthly users across 139-140 countries). Reelgood: Pro's $13.3M raised / $5.8M-$11.1M revenue / 30-60 employees vs. Flash's $13.3M-$15.4M raised (Flash itemizes a March 2022 $4.1M debt facility Pro folds into the total without naming) / ~$8.4M ARR (inside Pro's range) / 27-43 employees (overlapping, not identical, treat as estimate variance not conflict). Sensor Tower: Pro's $1M seed independently confirmed correct via AngelPad's own blog (Sensor Tower's actual seed was $1M in August 2013, led by Rembrandt Venture Partners); Flash doesn't restate that seed round by name but its "bootstrapped through year five, minimal dilution" framing is fully consistent with it, an omission, not a conflict. Both agree on the May 2020 $45M Riverwood Series B and March 2024 data.ai acquisition; Flash adds acquisition-financing detail Pro doesn't have (Bain Capital Credit-led debt/equity syndicate, Riverwood's Francisco Alvarez-Demalde chairing the board, roughly 200 legacy data.ai layoffs).
2. Business model clarity: both agree, JustWatch is majority B2B programmatic media buying (JustWatch Media) rather than consumer affiliate fees, Reelgood is B2B metadata/data licensing (Flash adds the "Content Calculus" M&A due-diligence product as a named example).
3. Sensor Tower vs. Wallet layer: both give the same distinction, Wallet is realized transactional/billing data, Sensor Tower is pre-transaction app-intelligence borrowed as a CAC proxy. Flash names the specific mechanisms in more depth, app-store download velocity as a subscriber-addition proxy, "Power User" session-frequency tracking as a churn proxy, Pathmatics ad-spend tracking for CAC modeling.
4. Competitive entrants: **the two passes name almost entirely different AI-disintermediation entrants, complementary coverage rather than a conflict.** Pro names Tubi's native ChatGPT integration (April 7, 2026) and PlayPilot. Flash names Likewise's "Pix" (Bill Gates-backed, 600M data points, 6M users, SMS/email/CTV-native conversational recommendations) and Lumio's "Project Neo" (WhatsApp/Instagram-native agentic remote control), and adds Netflix's own internal generative-AI voice-search defense as a platforms-fight-back angle. Both name Frenzi (Mumbai, Gen-Z-focused AI search), the one point of overlap. Together the two passes cover materially more of the real competitive landscape than either alone.
5. Documented predictive accuracy: **Flash adds two new, fully sourced case studies beyond Pro's two.** Pro has Disney+'s Q4 2019 launch (35M downloads, $97.2M mobile ad spend, Sensor Tower) and Netflix's Q2 2022 subscriber contraction (Hedgeye's Sensor Tower analysis showing the worst US download quarter since Q4 2014, corroborated by Antenna's churn data). Flash corroborates the Netflix Q2 2022 case with matching figures and adds two Pro doesn't have: JustWatch's Q1 2026 watchlist-intent data predicting Disney+ (16%) and Apple TV+ (12%) narrowing the market-share gap with Netflix (19%) and Prime Video (17%), and Sensor Tower's 2025-2026 "micro-drama engagement inversion" (ReelShort's 35.7 daily minutes per US user outpacing Prime Video's 26.9, Netflix's 24.8, and Disney+'s 23). Flash omits the Disney+ 2019 case entirely, an omission rather than a conflict.

**Corroborated across both variants**
Netflix's Q2 2022 subscriber-contraction case and its underlying Sensor Tower download-velocity mechanism; Sensor Tower's May 2020 $45M Riverwood Series B and March 2024 data.ai acquisition; JustWatch's and Reelgood's B2B (not affiliate) business models; Frenzi as an AI-native discovery entrant.

**Unique to one variant only**
- Pro only: the Disney+ Q4 2019 launch case study; Tubi-ChatGPT integration and PlayPilot as named AI entrants.
- Flash only: Likewise/Pix and Lumio/Project Neo as named AI entrants; Netflix's internal generative-AI defense; the JustWatch Q1 2026 market-share-shift case study; the micro-drama engagement-inversion case study; Reelgood's March 2022 debt facility and "Content Calculus" product; data.ai acquisition financing detail.

**Conflicts / fault lines**
None found. Every apparent divergence (funding totals, employee ranges, which AI entrants get named) resolves to normal estimate variance or complementary coverage once checked, including an independent check on Sensor Tower's seed round via AngelPad's own blog.

**Recommended integration approach**
Merge rather than pick a base, this is the one layer in the whole review where two variants are genuinely additive with essentially nothing to adjudicate. Use Pro's structure and fold in Flash's AI-disintermediation and predictive-accuracy sections as direct additions rather than replacements.

**Notable findings**
JustWatch's founding team and February 2015 US/Germany launch, CEO David Croyé's kaufDA-sale-funded bootstrap (Flash); Reelgood's Distribution Arc data (median SVOD-to-AVOD window dropped from 6 months in 2020 to 2.5 months in 2025) and full five-round financing detail (Pro totals, Flash itemizes); Disney+ Q4 2019 35M downloads / $97.2M mobile spend (Pro, via Sensor Tower/MediaPost/AnimationXpress); Tubi-ChatGPT integration April 7, 2026 (Pro, Fox Corp/OpenAI); JustWatch's Q1 2026 watchlist-intent market-share data and Sensor Tower's micro-drama engagement-inversion data (both Flash).

**Internal quality flags**
Several core figures in both variants rest on aggregator/estimator sites (Kona Equity, Growjo, Tracxn) rather than primary company disclosure, unavoidable given both JustWatch and Reelgood are private. Employee counts and revenue figures for both are analyst estimates without a named primary filing in either variant.

**Gaps remaining**
Objective 3's claim that Sensor Tower's primary streaming-specific client base is broad app-economy intelligence, not streaming-exclusive, is still asserted rather than confirmed via a named client in either variant. Revenue-figure sourcing for JustWatch and Reelgood still rests on estimator sites in both variants.

**Gaps remaining**
Objective 3's "confirm primary client base" instruction is only partially met.

---

## 7. Layer 6: Sports-Rights Sub-Vertical

Three Pro-tier passes. Filename numbering does not match creation order: the file named "Sports Rights Layer" (no suffix) was actually created first (02:34 UTC), "Sports Rights Layer 3" second (16:50 UTC), and "Sports Rights Layer 2" third and latest (16:51 UTC, one minute after "3"). Referred to below by creation order (Run A = unsuffixed/earliest, Run B = "3", Run C = "2"/latest) to avoid the filename confusion propagating into the master file.

This is the densest prompt file of the eight (10 numbered objectives), several tied to local cross-references the research was explicitly told not to re-derive.

**Objective coverage**
1. Stats Perform/FIFA execution: Run C alone answers the "issues/challenges" half (xGOT model, May 2026 FIFA Integrity Task Force with FBI/INTERPOL/UNODC/Sportradar/Genius, no reported breaches as of research date). Runs A and B cover only deal terms.
2. SIL/Zoomph one year on: Run A gives generic ROI stats; Run B names brands broadly (Legends, Kellanova, NASCAR, Monumental); Run C is the only one naming specific late-2025 clients (Washington Wizards, all 12 WNBA teams, Ally Financial's 50/50 pledge). Run C best.
3. Streaming platforms' in-house data ambitions: Run A is descriptive only. Runs B and C both explicitly frame build-vs-buy and converge on the same answer (build in-house for ad targeting/personalization, stay dependent on the triopoly for certified betting/integrity data); Run C adds a concrete Amazon-NBA illustration.
4. Betting-handle correlation, named operator: Runs A and C both cite the Sportradar-Kalshi deal (June 2026); Run B omits Kalshi and gives an industry GGR revenue-share range instead. None discloses actual dollar terms for a single deal.
5. Competitive landscape/toll-layer verification: Run C most complete (names holders and dates for UEFA, Bundesliga, NASCAR, NHL, MLB, NBA); Run B adds NCAA/CFP detail; Run A thinnest.
6. NHL, CFP, Savannah Bananas: Run A addresses none of the three; Run B partial; Run C decisive on all three, including the CFP's split between SportSource Analytics (certified committee provider) and Genius's NCAA LiveStats.
7. Journalism track: Run A silent; Run B vague; Run C fully answers all three sub-asks, including a $60M/3-year Barstool deal.
8. ESPN Unlimited to MLB.tv/NBA League Pass: Run A silent; Run B offers only generic language; Run C gives a concrete mechanism (MyDisney account linking) and MLB.TV pricing, but no variant addresses NBA League Pass specifically.
9. Sequencing conflict: Run A silent; Runs B and C both independently resolve to the same order (see fault line below).
10. Fox One pricing/Roku: Run A silent; Runs B and C conflict materially (see fault lines); Run C alone covers the Fox-Roku acquisition.

**Corroborated across all/most variants**
Stats Perform/FIFA January 2026 exclusive deal, 48-team/104-match 2026 World Cup, Opta plus RunningBall dual engine, Bet LiveStreams. Sportradar Q1 2026 financials (revenue roughly €346.5-347M, +11% YoY, Adj. EBITDA €66.0M/19% margin). Genius Sports Q1 2026 financials (Group Revenue $188.0M, +31% YoY, Adj. EBITDA $24.0M). SIL-Zoomph partnership dated April 2025; Genius acquired SIL September 2025. Tickers: Genius NYSE:GENI, Sportradar Nasdaq:SRAD.

**Unique to one variant only**
- Run A: Paris 2024 Olympics cloud infrastructure detail, deep NFL Next Gen Stats technical detail, Netflix Open Connect engineering detail, industry-wide GGR revenue-share range (12-25%).
- Run B: broader alt-data taxonomy tying this layer to Layers 0, 1, 4, and 7; NCAA extension through 2032 with prop-bet ban detail; full regulatory-exposure section (Delete Act, CFPB 1033, VPPA, LiveRamp); Suits/Parrot Analytics case study.
- Run C: FIFA Integrity Task Force and xGOT/micro-betting framing; NHL's 2021 ten-year Sportradar extension through 2031-32; the CFP/SportSource-Genius LiveStats split; Savannah Bananas detail ($500M valuation, $17.1M single-weekend economic impact); full Barstool-Netflix terms; MyDisney/MLB.TV mechanism; Fox One's $19.99/$39.99 split; the $22B Fox-Roku acquisition terms.

**Conflicts / fault lines**
- **Fox One standalone price, fully resolved 2026-07-07.** Run B states $39.99 (conflates standalone Fox One with the ESPN-bundled tier). Run C states $19.99 standalone, $39.99 only when bundled with ESPN Unlimited. Reid supplied a fox.com pricing-page screenshot confirming Run C's reading in full: Fox One Subscription $19.99/month or $199.99/year standalone, Fox One + Fox Nation bundle $24.99/month, ESPN Unlimited + Fox One bundle $39.99/month, B1G+ (Big Ten Plus) add-on $12.99/month or $89.99/year on any plan. Run B's flat $39.99 framing is confirmed wrong, it was the bundle price mistaken for the standalone price. Run C is the correct base for this objective; the Fox One + Fox Nation and B1G+ tiers are new detail beyond what any of the three Deep Research passes surfaced.
- **Legend acquisition funding, resolved 2026-07-07.** This wasn't even a clean Run A vs. Run C conflict, both figures ("$850 million Term Loan B" and "$825 million term loan plus $220M revolver plus $800M cash plus 10.1M shares") actually appear inside the same document (Run A), in two different paragraphs that never reconcile with each other, most likely because Gemini pulled the $850M figure from earlier deal-announcement coverage and the $825M figure from later closing coverage without checking they were describing the same fact at two different points in time. Checked against the actual closing: Genius Sports' 6-K/credit-agreement disclosure (via SEC EDGAR, reported by Stock Titan and the Globe and Mail) confirms the final structure at close (April 30, 2026): $800 million cash plus 10 million-plus new shares as deal consideration, funded via a new credit agreement comprising an $825 million senior secured term loan (Term Loan A, not Term Loan B) at SOFR+350bps and a $220 million revolving facility, both maturing April 30, 2031. The $850 million Term Loan B figure was an earlier, superseded number from signing-stage coverage, not what actually closed. Use $825M term loan / $220M revolver / $800M cash / 10M+ shares as the settled figures.
- NBA-Sportradar rights term: Runs A and C both find the deal runs through the 2030-31 season, not "through 2032" as the objective's own framing (borrowed from the Great Collision post) assumed, suggesting a possible conflation with MLB's separate 2032 date. No variant flags this itself, it only surfaces by checking the objective against the research.
- **Sequencing conflict (objective 9), resolved 2026-07-07 with a primary-sourced timeline, no longer an open fault line.** Two independent Gemini passes (Runs B and C) both found ESPN Unlimited launched August 2025, with the YouTube TV blackout following in November 2025, three months later, as a distributor reaction rather than the cause, against `espn-retention-analysis.md`'s framing of the blackout as preceding and motivating the launch. Reid confirmed the Gemini reading directly and supplied a sourced timeline document (30 numbered citations, primary press and trade sources: ESPN.com, The Athletic, Deadline, Awful Announcing, Wikipedia) that supplies the mechanism the two passes only asserted without explaining: ESPN Unlimited launched August 21, 2025 without the leverage to dictate cable-carriage terms, then built that leverage afterward through the NFL's 10% ESPN equity stake plus the NFL Network/RedZone acquisition, the $325M/year WWE rights deal, and a CW sublicensing pact for ACC/Mountain West/Pac-12 games. Every other major distributor (Charter Spectrum, DirecTV, Fubo, Cox) folded and granted authenticated app access to their pay-TV subscribers at no extra charge; Google did not, which produced the two-week blackout. Resolution: YouTube TV agreed to fully integrate ESPN Unlimited into its base-plan subscriber UI (Deadline, Nov 2025). `espn-retention-analysis.md` still states the sequence backwards and should be corrected to match, that correction was flagged to Reid but not made in this pass, no edits to that file were made without his direct instruction.
- Minor rounding only: Sportradar Q1 figures vary trivially between Run A (€347M/€6M/€9M) and Runs B/C (€346.5M/€6.3M/€9.3M).

**Recommended integration approach**
Use Run C as the base, it leads or ties on nearly every objective. Pull from Run A: the Paris 2024/Next Gen Stats/Open Connect technical-infrastructure background, and the 12-25% GGR revenue-share range. Pull from Run B: the taxonomy paragraph cross-referencing this layer into the framework's broader architecture, the NCAA-2032 extension detail, and flag its regulatory-exposure section as likely belonging to the Identity/Clean Rooms or Wallet layer rather than Layer 6, pending a scope call. For objective 9 specifically, fold in Reid's sourced timeline doc (dated 2026-07-07, cited above) rather than either Gemini pass alone, it is the only one of the three sources that explains the leverage-building mechanism rather than just asserting the date order.

**Gaps remaining**
No variant addresses the NBA League Pass connection mechanism (only MLB.tv covered). No variant discloses actual dollar-value commercial terms for a single sportsbook data deal. The "400+ leagues" aggregate claim from the toll-layer thesis is never tallied or verified. Objective 9's ask for another rights holder running a comparable playbook is answered only generically (WBD, PSKY named) without a dated, concrete parallel case. `espn-retention-analysis.md`'s launch/blackout sequencing was corrected 2026-07-07 (Section 5's Content Fortress Playbook steps re-ordered to match the actual timeline), that correction is now made, not just flagged.

---

## 8. Layer 7: Identity Resolution & Clean Rooms

Two unlabeled passes, 01 (2026-07-07 12:09 UTC) and 02 (12:18 UTC, roughly 9 minutes later).

**Objective coverage**
1. LiveRamp/Publicis deal status: both confirm the same core terms ($38.50/share, 29.8% premium, $2.167B EV/$2.546B equity, Aug 17 2026 vote, HSR/CFIUS pending, still pending not closed). Run 01 is stronger on deal mechanics and regulatory timeline (break fee $32.35M, HSR filed June 11 2026, Johnson Fistel investigation). Run 02 is far stronger on client-attrition commentary, naming WPP CEO Cindy Rose's on-record Cannes Lions confirmation (full exit to InfoSum) and Omnicom's Q1 2028 planned exit to its own Real ID, both absent from 01. Neither variant re-verified deal status was still current as of its own research date; that check was done 2026-07-07 against Publicis Groupe's own press release and confirmed nothing has changed (see Gaps remaining).
2. UID2 trajectory/TTD reaction: 01 covers UID2 scale (200+ publishers) and, uniquely, the full Publicis-TTD audit dispute (fee-stacking allegation, 13% stock hit, June 12 resolution). 02 covers the same June 12 reaffirmation but omits the dispute backstory, adding unique detail on TTD's Kokai/Koa Agents and Open Agentic Kit (Anthropic Claude integration). Combined, complete.
3. AMC vs Walmart Connect economics: both attempt AMC-specific quantification but diverge (see fault lines). Neither cites a true AMC-only revenue line, both proxy with total Amazon ad revenue.
4. New entrants/agentic identity protocols: complementary. 01 covers commerce-transaction protocols (UCP, ACP, MCP). 02 covers agent-identity/auth protocols (AgentID/IETF draft, OAuth 2.1 PKCE, SPIFFE/SPIRE, Ping "Identity for AI") plus Omnicom's disclosed direct-to-publisher AI agent buys.
5. Comscore CustomIQ: both corroborate the recap, McLaughlin/Frankel, 99.5% match rate. 02 uses the rubric's own language and adds the Movies divestiture and 89.8% email-only match rate. 01 adds an AI-assistant traffic table not in 02.

**Corroborated across both variants**
$38.50/share, 29.8% premium (vs $29.66 close, May 15 2026), $2.167B EV / $2.546B equity, 66 2/3% shareholder vote, Aug 17 2026 special meeting, Evercore fairness opinion, HSR/CFIUS required, target close by end of 2026, WPP-InfoSum (April 2025) and Omnicom-IPG/Acxiom (2025) consolidation, Comscore recap closed Dec 29 2025 ($18M dividend eliminated), McLaughlin (ex-DoubleVerify COO) as CEO, Frankel to board, CustomIQ's 99.5% Full-PII match-rate validation of LiveRamp, June 12 2026 Publicis-TTD reaffirmation.

**Unique to one variant only**
- 01 only: Publicis M&A buildup (Epsilon, CitrusAd, Profitero, Lotame), full TTD audit-dispute narrative, break fee, HSR filing date, Johnson Fistel investigation, UCP/ACP protocols, AI-assistant traffic table.
- 02 only: financing structure (bonds, 1.2x leverage, $126M EBITDA, $50M synergies, BBB+/Baa1 ratings), shares outstanding (60,786,315), named WPP/Omnicom/ID5/CleanTap/Ray Media/Unity CRO reactions, Koa Agents/Open Agentic Kit, AgentID/NHI protocol stack, Omnicom's disclosed AI-agent media buys, Comscore Movies divestiture, 89.8% email-only match rate.

**Conflicts / fault lines**
- **Amazon total ad revenue, resolved 2026-07-07.** 01 says TTM >$70B (Q1 2026 $17.2B); 02 says ">$50B annually in 2026, up from $38B in 2023." Verified directly against Amazon's own Q1 2026 earnings release (Andy Jassy's own quote: "Advertising grew to over $70 billion in TTM revenue," Q1 2026 ad revenue $17.24B, +24% YoY): 01 is correct and current, 02 is stale by roughly $20 billion. Same conflict as Layer 0's review above, resolved there once, cross-referenced here rather than re-litigated.
- **Walmart Connect revenue, resolved 2026-07-08.** 01 gives FY2025 "$4.4B US / $6.4B global (+24%/+46%)"; 02 and the Layer 4 Pro docx both give ">$4.8B in 2025 (+30% YoY)" with no US/global split. Checked against Walmart's own SEC 8-K earnings releases and earnings-presentation exhibits for both fiscal years (FY25 8-K, sec.gov/Archives/edgar/data/0000104169/000010416925000010; FY26 8-K, sec.gov/Archives/edgar/data/0000104169/000010416926000095, corroborated by Marketing Dive, AdExchanger, and Adweek coverage of the same releases): actual reported figures are FY2025 global ad revenue $4.4 billion (+27% full year, Walmart's fiscal year ends January 31), and FY2026 global ad revenue $6.4 billion (+46% YoY), with Q4 FY2026 U.S. Walmart Connect growth of 41%. So 01's $4.4B figure is real but mislabeled, it's FY25 *global*, not U.S., revenue. 01's $6.4B figure is real but misdated, it belongs to FY26, not FY25. 02's $4.8B figure doesn't match any of Walmart's own disclosures in either fiscal year and should be dropped. Use the corrected pairing in the integrated layer file: FY25 global $4.4B (+27%), FY26 global $6.4B (+46%, Q4 U.S. Walmart Connect +41%), both cited to Walmart's own SEC filings rather than either docx's secondary-blog citation.
- **AMC free-tier mechanics, resolved 2026-07-08.** 01 says 1P signals free June 1 through Dec 31, 2026 (time-limited promotion); 02 says free on an ongoing basis for any advertiser with an active DSP MSA, no expiration stated. Confirmed directly against Amazon's own AMC documentation page (advertising.amazon.com, "Paid features overview," fetched and read in full 2026-07-08): "Starting June 1, 2026, all Amazon 1P signals covered under AMC Paid Features...will be available to query at no cost through December 31, 2026 in all regions where AMC Paid Features are available." 01 is correct, this is an explicitly time-limited promotion with a stated end date, not a permanent MSA-conditioned policy. 02 is wrong on the framing (permanent vs. promotional) even though its underlying point, that eligible advertisers don't pay extra right now, is directionally true for the remainder of 2026. Use 01's framing and the December 31, 2026 sunset date in the integrated layer file, and flag it as a date to revisit since the promotion's fate after that isn't stated on the page.
- The deal-financing detail in 02 (leverage, EBITDA, synergies) is entirely uncorroborated by 01, flag as single-source pending a second check.

**Recommended integration approach**
Use 02 as the base for the Publicis/LiveRamp section given its stronger sourcing on client attrition (the objective flagged in the prompt file as highest priority) and deal financing. Pull into it from 01: the TTD audit-dispute narrative (contextualizes the June 12 reaffirmation as a resolution, not a steady state), the Johnson Fistel investigation, HSR filing date and break fee, and the AI-assistant traffic table for the Comscore section. For deal terms specifically, Publicis Groupe's own press release (publicisgroupe.com, 2026-05-17) confirms both variants' $2.167B EV / $2.546B equity / $38.50 per share / 29.8% premium figures exactly, use it as the anchor citation over either variant.

**Gaps remaining**
**Deal status re-confirmed 2026-07-07, no longer an open gap.** Signed 2026-05-17, not yet closed, still subject to regulatory approval and a LiveRamp shareholder vote, targeted to close before year-end 2026, per Publicis Groupe's own press release. No reported change in terms, competing bid, or regulatory objection as of this check. No variant isolates a true AMC-only revenue figure, that gap remains open, not independently verified in this pass.

---

## 9. Cross-layer notes surfaced during this review

Two facts recurred across layer boundaries. Both were checked once against primary sources on 2026-07-07 rather than resolved twice:

- **Amazon total ad revenue, resolved.** Conflicted the same way in the Layer 0 review (">$50B" vs "$70B TTM") and the Layer 7 review (">$50B, up from $38B in 2023" vs "TTM >$70B"). Amazon's own Q1 2026 earnings release (aboutamazon.com, April 29, 2026) settles it: Andy Jassy's own words, "Advertising grew to over $70 billion in TTM revenue," with Q1 2026 advertising services revenue of $17.24B, +24% YoY. The "$70B TTM" reading is correct and current in both layers; the ">$50B" reading is stale by roughly $20 billion.
- **LiveRamp/Publicis deal price, resolved, and it was never actually a conflict.** The $2.54B-vs-$2.16B spread in the Layer 0 gatekeeper review, and the figures anchoring the entire Layer 7 review, are both correct: Publicis Groupe's own press release (publicisgroupe.com, 2026-05-17) states enterprise value $2.167 billion and total equity value $2.546 billion, with $379 million in acquired net cash bridging the two ($2.546B minus $379M equals $2.167B, exactly). Every variant that quoted one of these figures was right, none flagged which of the two it was quoting. Use $2.167B for enterprise value and $2.546B for equity value going forward, matching the main map's own Section 4 figure.
- Every layer that touches Fox (0, 6) independently surfaced the Fox-Roku $22B acquisition with matching terms across variants, this one has no fault line, treat it as settled.

---

## 10. Provenance

This map was built by reading all 17 Gemini Deep Research docx outputs in `supporting/` against the numbered research objectives in the corresponding `layers/00-gatekeeper-layer.md` through `layers/07-identity-clean-rooms-layer.md` prompt files, then diffing same-layer variants against each other. No source docx, no layer prompt file, and no other existing framework document was edited to produce this map. Nothing above is new research, every fact traces to one of the 17 existing documents; where variants disagree, both readings are recorded rather than adjudicated, consistent with the fault-line convention already in use in `streaming-altdata-ecosystem.md` Section 6. The Google Drive copies of these same 17 documents were confirmed to match the local `supporting/` docx set 1:1 by file name before this review started, the local docx set is the one actually reviewed.

This document does not itself update `streaming-altdata-ecosystem.md` or any `layers/*.md` file. It is the guide for that integration pass, not the integration itself.

**2026-07-08 addendum.** Reid supplied four additional MD-format Deep Research outputs for Layers 2 (Glass), 3 (Shield), and 5 (Funnel), landing as a second variant for each of those three layers (previously single-source). Two of the four uploads are a byte-identical duplicate of the same Glass Layer pass (confirmed by checksum), so three distinct new documents in substance. Per Reid's instruction, these were reviewed the same way as the original 17: compared objective-by-objective against the existing summaries, with one real fault line found (Layer 2, EDO v. TVision misattributed, corrected to Nielsen v. TVision) and independently verified against primary sources (CourtListener, Cohen Milstein, Viant's own SEC 8-K, AngelPad's own blog) before folding in. Sections 3, 4, and 6 above, plus the Section 0 summary table, were updated accordingly; no other section changed. As of this addendum, these four files remain in Reid's Downloads folder, not yet moved into `supporting/`, per his instruction not to archive them until this review confirmed they were worth keeping. They are worth keeping. Move the three distinct documents into `supporting/` (retire or discard the duplicate upload) whenever convenient, ideally before the next session runs the actual layer-integration pass, so that session's file inventory matches what this map now describes.
