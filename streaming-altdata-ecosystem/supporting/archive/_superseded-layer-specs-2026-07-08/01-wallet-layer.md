# Layer 1: Wallet, Subscriber Transaction Intelligence (Master Findings)

> **Document type:** Master findings file (Deep Research integration), not a prompt file and not the diff map.
> **Created:** 2026-07-08, integration pass
> **Sources:** four Gemini passes across four model tiers: Pro (2026-07-06), Finance, Flash, FlashLite (all three 2026-07-07 midday, roughly 90 seconds to 2 minutes apart)
> **Base document:** Pro, per `DEEP-RESEARCH-DIFF-MAP.md` Section 2
> **Readiness:** merged, two fault lines remain open

---

## 1. Findings by research objective

**1. Ownership and capital structure.** YipitData: Carlyle led a $475 million Series E (December 2021), Norwest put in $175 million (2019), a CIBC debt facility closed June 2024, institutional investors hold 60-75% of voting power, and YipitData acquired 1010data in 2023. IPO status is a genuine sourcing-quality fault line (Section 4). The most current fact in the set: Henry Schuck, CEO of ZoomInfo, joined YipitData's board April 13, 2026.

**2. Margin compression and the Plaid precedent.** JPMorgan Chase and Plaid's renewed data-access agreement charges per data pull for the first time, a structural shift from fixed to variable cost across the Wallet layer. No pass confirms Bank of America, Wells Fargo, or Citi have activated identical per-pull fees yet, only directional commentary. The furthest anyone gets: PNC executives Demchak and Overstrom are on record endorsing the tolling model and directing clients to Akoya, and Bank of America has an early-2026 API migration timeline in motion.

**3. DROP compliance.** The Delete Request and Opt-Out Platform's August 1, 2026 enforcement deadline hasn't passed as of any research date, and no Wallet-layer vendor by name has a cited deletion failure. The compliance-infrastructure-is-active argument is well supported by real CPPA registration-failure fines against non-Wallet-layer brokers: S&P Global, Rickenbacher/Datamasters, and Jerico Pictures. Fine amounts themselves carry a minor open discrepancy (Section 4).

**4. Subscriber Views depth.** No pass confirms public pricing or a named client roster for Antenna's Subscriber Views product. The best available data point is a CLTV case study showing $186.71 versus $122.48, the most granular figure on the product across all four passes. Pricing itself is disputed (Section 4).

**5. Consumer Edge/Earnest fusion.** All four passes converge: partial integration, not a fused product. The clearest mechanistic explanation is HIPAA de-identification requirements and schema incompatibility keeping the two panels separately siloed even after the April 2025 acquisition. A June 2026 combined forecasting report complicates the "still siloed" conclusion somewhat, suggesting the fusion is further along operationally than the underlying data architecture would imply.

**6. New entrants and exits.** The weakest-answered objective across all four passes. No pass identifies a new zero-party entrant disrupting the incumbent hierarchy. The closest anyone gets to fresh detail here is a set of named exit/M&A events, technically outside strict Wallet-layer scope but adjacent enough to be worth carrying (Section 3).

---

## 2. Corroborated across all or most variants

YipitData's capital history above. Consumer Edge acquired Earnest Analytics in April 2025 (bringing in Orion/Vela, Phoenix Pharmacy Claims, and Leo Medical Claims). Antenna: backed by BDMI, Raine, and Foundry Group; its Subscriber Views product fuses ACR tuning data with transaction-panel data; the "Stick" feature drove roughly 33% (700,000) of Apple TV+ signups in June 2025; the Tampa Bay Buccaneers case study showed 98% versus 92% retention.

JPMorgan-Plaid: a roughly $300 million potential annual fee estimate (Forbes), described as "fractions of a cent per pull," with Plaid absorbing the cost for now. CFPB Section 1033 remains blocked by Judge Danny Reeves (October 2025). DROP: $200 per day per violation, a 45-day query cycle, the August 1, 2026 enforcement trigger, and over 215,000 California registrants by mid-2026 (Finance and Flash agree on this count).

---

## 3. Additional detail pulled in from FlashLite, Flash, and Finance (per the recommended integration approach)

Pro is the base, chosen for its structure, prose register, and 26-source bibliography. Three tiers add material Pro lacks:

From FlashLite: Henry Schuck's board appointment (April 13, 2026); the YipitData/ANSR India Global Capability Center partnership; the DROP enforcement examples (flagged as an open dollar-figure discrepancy, see Section 4).

From Flash: the HIPAA/Datavant explanation for why Consumer Edge and Earnest remain functionally siloed despite the acquisition; the CLTV case study ($186.71 versus $122.48); and a named M&A exit list (Novacap/IAS $1.9 billion, Mediaocean/Innovid, Comscore/Advaya $70 million, Ampere/PlumResearch), labeled adjacent-layer rather than strict Wallet-layer material since most of these sit in Glass, Shield, or Demand/Valuation.

From Finance: a zero-party platform comparison table (Fetch 17M+, Ibotta 40M+, Rakuten, Shopkick, Receipt Hog, with user counts) and the CoVenture $60 million funding round for Consumer Edge (January 2023).

A model-tier note worth carrying forward: Pro is not clearly the strongest pass on hard facts, it's the most sophisticated on synthesis and framing (the cross-layer triangulation methodology, the AI-native disruption thesis touching Gemini/Google Pay and OpenAI agentic shopping as a long-term Wallet-layer threat) but thinner on checkable specifics than Flash or FlashLite. Finance's sourcing is the weakest of the four (3 works cited versus 26-34 in the others) despite confident-sounding tables; its unique claims should be treated with more caution than the other three tiers'.

---

## 4. Fault lines

**Resolved by sourcing-quality check, not external verification (see the note on scope below):**

YipitData's IPO status. Pro and Flash say no S-1 has been filed, the company remains in preparation. Finance says a confidential S-1 has been submitted and the IPO is stalled pending market conditions. Checking each claim against its own citation: Pro and Flash both trace their "no S-1" reading to aggregator/marketplace profiles (PitchBook, Built In, EquityZen), the right kind of source for a company-status claim even if not definitive. Finance's "confidential S-1 submitted" claim traces to a single citation, a Hiive pre-IPO share-price listing page, a private secondary marketplace with no visibility into confidential SEC filings and no plausible way of actually knowing that fact. That citation cannot support the claim attached to it. Weight of evidence and citation quality both favor "no S-1 filed as of each variant's research date." Treat Finance's claim as unreliable rather than as a genuine competing data point. This is a within-document citation check, not a fresh external verification; a real SEC EDGAR confidential-draft disclosure check is warranted if IPO timing becomes decision-relevant.

**Open, recorded rather than resolved:**

Subscriber Views pricing. Flash says "mid-six-to-seven-figure" annual commitments. FlashLite says "low-to-mid six figures." A materially different magnitude claim for an undisclosed figure, and neither is sourced to a named client contract. Open.

DROP enforcement fine amounts. Flash says Rickenbacher was fined $42,000 and S&P Global $62,000. FlashLite says Rickenbacher $45,000 and S&P Global $62,600. Same two enforcement actions, different dollar figures in each pass. Open, minor.

Two smaller, lower-stakes discrepancies worth noting without elevating to full fault-line status: JPMorgan's request volume (Pro: 1.89 billion requests in June 2025 specifically; Finance: "approximately two billion monthly, up from one billion in 2023," a different framing and base period) and Bloomberg Second Measure's acquisition date (Finance and Flash: "late 2020"; FlashLite: December 24, 2020 specifically, while also flagging what looks like a database error conflating a re-parsed 2019 Series A with a phantom "2026 Series A").

---

## 5. Gaps remaining

No pass produces a confirmed dollar figure any Wallet-layer vendor other than Plaid is actually paying banks for data access. No pass names a specific, confirmed Subscriber Views client. No pass confirms or denies Bank of America, Wells Fargo, or Citi per-pull fees with a primary source, only directional commentary. No pass identifies a genuinely new zero-party entrant disrupting the incumbent hierarchy since mid-2026.

---

## 6. Provenance

Synthesized from `DEEP-RESEARCH-DIFF-MAP.md` Section 2 (four Gemini passes across four model tiers, 2026-07-06 and 2026-07-07). No new research performed in this integration pass. Fault-line convention follows `streaming-altdata-ecosystem.md` Section 6.
