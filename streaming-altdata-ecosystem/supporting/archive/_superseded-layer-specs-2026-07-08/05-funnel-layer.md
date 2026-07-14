# Layer 5: Funnel (Downstream Intent & Discovery) (Master Findings)

> **Document type:** Master findings file (Deep Research integration), not a prompt file and not the diff map.
> **Created:** 2026-07-08, integration pass
> **Sources:** two Gemini passes, Pro (original) and Flash (added 2026-07-08, uploaded as "05 - Deep Research - Flash - Funnel Layer.md")
> **Base document:** merged, not a base-plus-pull situation, both variants are genuinely additive
> **Readiness:** ready to merge, no fault lines. The prompt file flagged this layer as most likely to come back thin; neither pass did, and Flash held up well against Pro, consistent with this review's recurring finding that cheaper Gemini tiers are surprisingly competitive.

---

## 1. Findings by research objective

**1. Ownership and scale, from scratch.** Both passes deliver on all three vendors, matching within normal estimate variance. JustWatch: Pro's roughly $68 million 2026 revenue estimate sits inside Flash's $50 million to $100 million range; Pro's 200-243 employees matches Flash's "exceeding 200" (Flash adds the growth curve: 56 employees in 2020 to 200-plus by 2026, across eight offices and 46 nationalities, plus 50 million-plus monthly users across 139-140 countries). Reelgood: Pro's $13.3 million raised, $5.8 million to $11.1 million revenue, 30-60 employees, versus Flash's $13.3 million to $15.4 million raised (Flash itemizes a March 2022 $4.1 million debt facility that Pro folds into the total without naming), roughly $8.4 million ARR (inside Pro's range), and 27-43 employees (overlapping, not identical, treated as estimate variance rather than conflict). Sensor Tower: Pro's $1 million seed round is independently confirmed correct via AngelPad's own blog (Sensor Tower's actual seed was $1 million in August 2013, led by Rembrandt Venture Partners); Flash doesn't restate that seed round by name, but its "bootstrapped through year five, minimal dilution" framing is fully consistent with it, an omission rather than a conflict. Both passes agree on the May 2020 $45 million Riverwood Series B and the March 2024 data.ai acquisition; Flash adds acquisition-financing detail Pro doesn't have (a Bain Capital Credit-led debt/equity syndicate, Riverwood's Francisco Alvarez-Demalde chairing the board, roughly 200 legacy data.ai layoffs).

**2. Business model clarity.** Both passes agree: JustWatch is majority B2B programmatic media buying (JustWatch Media) rather than consumer affiliate fees, and Reelgood is B2B metadata/data licensing (Flash adds the "Content Calculus" M&A due-diligence product as a named example of that licensing business in practice).

**3. Sensor Tower versus the Wallet layer.** Both passes draw the same distinction: Wallet is realized transactional/billing data, Sensor Tower is pre-transaction app-intelligence borrowed as a customer-acquisition-cost proxy. Flash names the specific mechanisms in more depth: app-store download velocity as a subscriber-addition proxy, "Power User" session-frequency tracking as a churn proxy, and Pathmatics ad-spend tracking for CAC modeling.

**4. Competitive entrants.** The two passes name almost entirely different AI-disintermediation entrants, complementary coverage rather than a conflict. Pro names Tubi's native ChatGPT integration (April 7, 2026) and PlayPilot. Flash names Likewise's "Pix" (Bill Gates-backed, 600 million data points, 6 million users, SMS/email/CTV-native conversational recommendations) and Lumio's "Project Neo" (WhatsApp/Instagram-native agentic remote control), and adds Netflix's own internal generative-AI voice-search defense as a platforms-fight-back angle. Both name Frenzi (Mumbai, Gen-Z-focused AI search), the one point of overlap. Together the two passes cover materially more of the real competitive landscape than either alone would.

**5. Documented predictive accuracy.** Flash adds two new, fully sourced case studies beyond Pro's two. Pro has Disney+'s Q4 2019 launch (35 million downloads, $97.2 million mobile ad spend, via Sensor Tower) and Netflix's Q2 2022 subscriber contraction (Hedgeye's Sensor Tower analysis showing the worst US download quarter since Q4 2014, corroborated by Antenna's churn data). Flash corroborates the Netflix Q2 2022 case with matching figures and adds two Pro doesn't have: JustWatch's Q1 2026 watchlist-intent data predicting Disney+ (16%) and Apple TV+ (12%) narrowing the market-share gap with Netflix (19%) and Prime Video (17%), and Sensor Tower's 2025-2026 "micro-drama engagement inversion" (ReelShort's 35.7 daily minutes per US user outpacing Prime Video's 26.9, Netflix's 24.8, and Disney+'s 23). Flash omits the Disney+ 2019 case entirely, an omission rather than a conflict.

---

## 2. Corroborated across both variants

Netflix's Q2 2022 subscriber-contraction case and its underlying Sensor Tower download-velocity mechanism. Sensor Tower's May 2020 $45 million Riverwood Series B and March 2024 data.ai acquisition. JustWatch's and Reelgood's B2B (not affiliate) business models. Frenzi as an AI-native discovery entrant.

---

## 3. Merged content (both variants genuinely additive, per the recommended integration approach)

This is the one layer in the whole review where two variants are additive with essentially nothing to adjudicate. Pro supplies the structure; Flash's AI-disintermediation and predictive-accuracy sections are folded in as direct additions rather than replacements, already reflected in Section 1 above.

**Notable findings not otherwise captured in the objective-by-objective section:** JustWatch's founding team and February 2015 US/Germany launch, with CEO David Croyé's bootstrap funded by the earlier sale of kaufDA (Flash). Reelgood's Distribution Arc data showing the median SVOD-to-AVOD window dropping from 6 months in 2020 to 2.5 months in 2025, plus full five-round financing detail (Pro gives totals, Flash itemizes by round). Disney+'s Q4 2019 launch, 35 million downloads and $97.2 million in mobile ad spend (Pro, via Sensor Tower/MediaPost/AnimationXpress). Tubi's ChatGPT integration, April 7, 2026 (Pro, Fox Corp/OpenAI). JustWatch's Q1 2026 watchlist-intent market-share data and Sensor Tower's micro-drama engagement-inversion data (both Flash).

**Internal quality flags.** Several core figures in both variants rest on aggregator/estimator sites (Kona Equity, Growjo, Tracxn) rather than primary company disclosure, unavoidable given both JustWatch and Reelgood are private companies. Employee counts and revenue figures for both are analyst estimates without a named primary filing in either variant. Treat accordingly if this data ever feeds a decision-relevant estimate elsewhere in the tree.

---

## 4. Fault lines

None found. Every apparent divergence (funding totals, employee ranges, which AI entrants get named) resolves to normal estimate variance or complementary coverage once checked, including an independent check on Sensor Tower's seed round via AngelPad's own blog.

---

## 5. Gaps remaining

Objective 3's claim that Sensor Tower's primary client base is broad app-economy intelligence rather than streaming-exclusive is still asserted rather than confirmed via a named client in either variant.

Revenue-figure sourcing for JustWatch and Reelgood still rests on estimator sites in both variants, not primary filings, since neither company is public.

---

## 6. Provenance

Synthesized from `DEEP-RESEARCH-DIFF-MAP.md` Section 6 (two Gemini passes, Pro and Flash; Flash added 2026-07-08). No new research performed in this integration pass. Fault-line convention follows `streaming-altdata-ecosystem.md` Section 6, though this layer produced none to record.
