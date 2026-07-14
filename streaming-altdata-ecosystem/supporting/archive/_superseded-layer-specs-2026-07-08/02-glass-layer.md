# Layer 2: Glass (Hardware / ACR) (Master Findings)

> **Document type:** Master findings file (Deep Research integration), not a prompt file and not the diff map.
> **Created:** 2026-07-08, integration pass
> **Sources:** two Gemini Pro-tier passes. Run 1 (original build); Run 2, added 2026-07-08, uploaded as two byte-identical files ("Glass Layer Research Brief Execution.md" and "02 - Deep Research - Pro v2 - Glass Layer.md"), confirmed identical by checksum and treated as one document
> **Base document:** Run 2, a near-strict superset of Run 1 once one correction is applied
> **Readiness:** clean two-variant merge, one fault line resolved, no open conflicts remaining

---

## 1. Findings by research objective

**1. Nielsen fault line.** Already resolved in Run 1 and fully corroborated by Run 2 on every date and figure: the MRC accreditation timeline, the March 3, 2026 marketplace update, the May 27, 2026 delay to August 31, 2026, and the VAB Gauge suppression dispute. Run 2 adds one fact Run 1 didn't have: Nielsen's separate Audio Diary service went on a six-month MRC accreditation hiatus, June 23 through December 23, 2026.

**2. VideoAmp/iSpot upfront share.** Substantially deepened by Run 2 with dated figures Run 1 lacked entirely: VideoAmp's trajectory from roughly $3 billion (2024) to a projected roughly $6 billion (2026), and iSpot's $128 million 2025 revenue (up 22% year over year) with influence over an estimated $18 billion to $22 billion of upfront spend across NBCUniversal, Paramount, and AMC Networks. Run 2 also covers Comscore's regulatory standing, fully JIC certified and MRC-accredited for Local TV Demographics since April 2025, an angle Run 1 never addressed.

**3. Samba TV / Inscape.** Corroborated on the Project Gravity launch: Run 1 dated it May 26, 2026, Run 2's own press-release citation dates it May 21, 2026, both inside the same week, treated as the same event. Run 2 adds ownership detail (August Capital, Union Grove, plus equity stakes held by Disney, IPG, and Warner Bros. Discovery, an estimated valuation around $750 million) and two named acquisitions (Semasio, October 2024; Bestever AI, June 2026). Run 2 also reframes Inscape's post-Walmart status as a dual-track strategy: external licensing to VideoAmp and iSpot continues at arm's length, alongside deep internal integration into Walmart Connect's closed-loop attribution (a 2026 IAB NewFronts joint presentation, a named L'Oréal shoppable-content pilot, a unified login rolled out across Vizio OS and "onn" TVs). This is a fuller picture than Run 1's framing of Inscape as purely arm's-length.

**4. EDO v. TVision, corrected.** Run 1 named the litigants as EDO Inc. v. TVision on Delaware docket 1:2025cv00575. That's wrong. The correct litigants are Nielsen v. TVision, on that same docket: five separate patent suits filed since 2021, a November 10, 2025 antitrust counterclaim from TVision, and a June 2026 jury verdict of non-infringement in TVision's favor. Confirmed directly against CourtListener (docket 1:25-cv-00575, "Nielsen Company (US), LLC v. TVision Insights, Inc.") and Cohen Milstein's own case-study page. Run 1 had the right docket number and the wrong plaintiff. Separately, and also new in Run 2: Viant Technology agreed to acquire TVision Insights for $40 million ($22.5 million cash, $17.5 million stock), independently confirmed via Viant's own April 15, 2026 8-K and press release, expected to close in Q2 2026 (Run 2's stated "early May 2026" close falls inside that window). Run 1's read that neither party had an acquisition or materially expanded footprint as of mid-2026 wasn't wrong for its own research date, it was simply superseded by an event roughly two and a half months later.

**5. Holding-company multi-currency commitment.** The objective Run 1 flagged as its weakest is substantially answered by Run 2: GroupM (WPP) formally designated VideoAmp a preferred currency for a significant share of its national commitments; Omnicom Media Group, IPG Mediabrands, Publicis Media, and Dentsu are named as having deeply integrated both VideoAmp and iSpot into 2027-upfront planning, bidding, and reconciliation workflows, with agency guidance treating a "Nielsen-only" publisher posture as a structural pricing disadvantage. This is the named, dated commitment Run 1 said didn't yet exist.

---

## 2. Corroborated across both variants

Nielsen's National Big Data + Panel accreditation and audit timeline in full. The VAB Gauge suppression dispute and its March 19, 2026 WSJ-leak figures (linear 47.4% versus streaming 41.9%). Samba TV's Project Gravity launch.

---

## 3. What Run 2 adds beyond Run 1 (per the recommended integration approach)

Run 2 is used as the base because it corrects Run 1's one factual error, closes Run 1's own flagged weakest objective, and adds material Run 1 lacked entirely. Nothing needs pulling forward from Run 1 specifically once the EDO/Nielsen correction above is applied; Run 1 contributes no distinguishing claim that survives independently.

Run 2's additions, beyond the items already folded into Section 1: a full VPPA circuit-split legal section that Run 1 never addressed despite it bearing directly on this layer's core legal exposure. The Second Circuit's broad reading in *Salazar v. NBA* versus the Sixth Circuit's narrower "consumer" definition in *Paramount* creates up to $2,500-per-violation liquidated-damages exposure, with the Sony and Vizio historical class-action record as the pattern this layer's ACR-consent posture sits inside. This is the same circuit split flagged as an active, unsettled front in `streaming-altdata-ecosystem.md` Section 5; this layer file is where the Glass-layer-specific exposure detail belongs.

Also unique to Run 2: Samba TV's ownership and acquisition detail, Comscore's regulatory status, and the Viant/TVision deal, all folded into Section 1 above.

---

## 4. Fault lines

**Resolved:** EDO v. TVision was misattributed in Run 1; the real litigants are Nielsen v. TVision. This was the only real conflict this layer produced. See Section 1, objective 4, for the full resolution and citations (CourtListener, Cohen Milstein, Viant's own SEC 8-K).

Everything else in this layer is Run 2 either corroborating Run 1 outright or adding new material without contradicting it. No other open fault lines.

---

## 5. Gaps remaining

Objective 2's "confirmed actual, not projected" 2026 upfront dollar results still isn't fully closed. VideoAmp's roughly $6 billion figure remains explicitly a projection in Run 2 as well as Run 1.

No named 2027 holding-company commitment exists yet for iSpot specifically, only for VideoAmp (via GroupM). If iSpot lands a comparable named holdco commitment, that would close the last piece of objective 5.

---

## 6. Provenance

Synthesized from `DEEP-RESEARCH-DIFF-MAP.md` Section 3 (two Gemini Pro-tier passes; Run 2 added 2026-07-08). No new research performed in this integration pass beyond what the diff map itself already verified (CourtListener, Cohen Milstein, Viant's SEC 8-K). Fault-line convention follows `streaming-altdata-ecosystem.md` Section 6.
