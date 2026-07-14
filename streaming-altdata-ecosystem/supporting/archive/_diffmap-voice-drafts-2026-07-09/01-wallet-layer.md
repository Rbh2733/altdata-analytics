# Layer 1: Wallet, Subscriber Transaction Intelligence (Master Findings)

> **Document type:** Master findings file, rebuilt from the four source research documents.
> **Created:** 2026-07-09. Supersedes the 2026-07-08 spec-style draft (archived), which restated merge logic without the underlying research content.
> **Sources:** four Gemini Deep Research passes across four model tiers: Pro (2026-07-06, base document), Finance, Flash, FlashLite (all three 2026-07-07 midday, roughly 90 seconds to 2 minutes apart).
> **Merge authority:** `DEEP-RESEARCH-DIFF-MAP.md` Section 2. Findings below are consolidated; pass-level attribution appears only in the Fault lines section and where a claim is single-sourced and uncorroborated.

---

## Layer mechanics (orientation)

The Wallet layer is the ground-truth stratum of the streaming alt-data ecosystem: where the Glass layer measures attention and the Demand layer measures intent, the Wallet layer isolates the billing relationship itself, built from aggregated and anonymized credit/debit card streams, direct bank API feeds, and digital invoice tracking. Four derived metrics carry the layer's institutional value:

- **Cohort survival curves.** Tracking a signup-month cohort's attrition over multiple years to model customer lifetime value.
- **Plan-mix migration.** Visibility into premium-to-ad-supported tier downgrades as platforms universally roll out ad tiers, and whether those transitions are revenue-accretive or dilutive.
- **Cross-platform wallet mapping.** When a consumer cancels one service, transaction data shows where the entertainment budget is reallocated, distinguishing isolated churn from broader discretionary contraction.
- **Serial-churner tracking.** Highly transient consumers who repeatedly cancel and resubscribe over twelve-month windows, a behavioral segment sized at an estimated $9 billion market opportunity.

These metrics feed cross-layer triangulation workflows: a title-level demand spike from attention-layer providers gets time-lagged against Wallet-layer retention or resubscription curves over defined lag windows, controlling for confounders such as concurrent price increases or a competitor's simultaneous tentpole release.

Macro context: mid-2026 projections size the total alternative data market between $17.78 billion and $30 billion by year end, the variance reflecting definitional strictness (the narrow investment-management-spend model projected $15.4 billion for 2025; per Ready Signal and Neudata market reports). The Wallet layer's distinguishing legal exposure within that market is financial-transaction consent, not device consent, which places it directly in the path of CFPB Section 1033 and California's Delete Act.

---

## Findings by research objective

### 1. Current ownership and capital structure

**YipitData** is the dominant multi-sector incumbent. Founded 2010 as a daily-deal aggregator on a roughly $1.3 million seed round, it pivoted to institutional research in 2013. Capital history, corroborated across all four passes: $6 million Series A led by RRE Ventures (2011); $175 million growth equity from Norwest Venture Partners (2019), valuing the company in the mid-hundreds of millions; $475 million Series E led by The Carlyle Group (December 2021, out of a $587.71 million total round per PitchBook-derived profiles), pushing valuation past $1 billion; acquisition of 1010data (2023), financed with a mix of cash and equity, which brought former 1010data backers onto the cap table while early angel stakes were bought out in secondaries (broker projections had the integration lifting annual recurring revenue growth 8 to 12 percent annually); and a conventional debt facility from CIBC Innovation Banking (June 2024; one pass dates it June 13) taken in place of further dilutive equity.

By late 2025, institutional stakes represented an estimated 60 to 75 percent of total voting power, with founders Vinicius Vacanti and James Moran retaining a roughly 20 to 30 percent aggregate stake and day-to-day control while preferred holders carry liquidation preferences, merger and dilution vetoes, and drag-along rights. Board seats include Jon Korngold (Carlyle Growth Equity) and Parker Barrile (Norwest); one pass, citing SEC proxy-adjacent filings, also names Carlyle executives Scott Hughes and Patrick McCarter on compensation and nominating committees. Carlyle's balance sheet ($477 billion AUM exiting 2025, $300 million fee-related earnings in Q1 2026 against a $132.2 million GAAP loss, per Carlyle filings) insulates the position from short-term volatility.

The 2024-2026 posture shifted from hypergrowth to margin optimization ahead of a liquidity event: targeted workforce reductions in late 2025, an ROI-before-spend mandate, hires of public-market-experienced CFOs. The rumored 2026-2027 IPO remains in the preparation phase with no S-1 filed (see Fault lines, resolved). Two facts postdate everything else in the set: on April 13, 2026, YipitData appointed Henry Schuck, founder and CEO of ZoomInfo (NASDAQ: GTM), to its board of directors (Business Wire / YipitData press release), and the company has partnered with ANSR to establish a Global Capability Center in India for engineering and data-processing scale. Shares trade on restricted secondary marketplaces (Hiive, EquityZen, Notice) subject to company approval and rights of first refusal.

**Consumer Edge**, the primary horizontal challenger, is backed by Treville Capital Group and took over $60 million in equity financing from CoVenture in January 2023 to fund its M&A strategy. That capital culminated in the April 2025 acquisition of Earnest Analytics (one pass dates it April 14, 2025), founded by Kevin Carson in 2012, bringing the Orion and Vela consumer spend panels, Phoenix Pharmacy Claims, and Leo Medical Claims databases under one parent (integration status in objective 5).

**Antenna** is the streaming-specific vertical specialist. Founded 2019, seeded by Raine Ventures, with a $10 million Series A in February 2022 led by Bertelsmann Digital Media Investments (BDMI) alongside Foundry Group, with UTA Ventures participating; total raised is approximately $13.8 million across two rounds, with a wider cap table including Grit Capital, Hyper, Imagination Capital, SK Ventures, and Waverley Capital. Antenna deliberately runs a leaner capitalization optimized for enterprise B2B data-as-a-service licensing to media corporate development teams, and pioneered the M+1 retention metrics used to track serial churners and bundle efficacy.

**Bloomberg Second Measure** is a wholly owned Bloomberg LP subsidiary, acquired in late 2020 (one pass specifies December 24, 2020, facilitated by Moelis & Company and SRS Acquiom; see Fault lines for the date discrepancy). It has no independent funding track: its feeds are integrated into the Bloomberg Terminal (ALTD and ECAN) and distributed via Bloomberg Data License, drawing on a US panel of over 20 million consumers with five-plus years of spend history. A database artifact reporting a "new" $20 million Series A in March 2026 traces to a re-parsed record of the actual February 12, 2019 Series A (co-led by Bessemer Venture Partners and Goldman Sachs, with Citi Ventures participating) and is an error, not a funding event.

**M Science** is a quant-focused, wholly owned subsidiary of Jefferies Financial Group (NYSE: JEF), which reported Q2 fiscal 2026 revenue of roughly $2.21 billion (up 35 percent year over year) and net income up 157 percent to $226.2 million. M Science has modernized delivery for the agentic era: a Unified Data Model plus a Model Context Protocol (MCP) server that lets autonomous AI systems programmatically query its analyst-curated datasets, converting a passive dataset into an API-callable knowledge graph.

### 2. Margin compression: the JPMorgan/Plaid precedent

The Wallet layer's economics historically rested on near-zero marginal-cost data acquisition through aggregators (Plaid, Yodlee, MX, Finicity), much of it via screen-scraping. That paradigm has collapsed. In July 2025 JPMorgan Chase sent commercial pricing sheets to major aggregators; in September 2025 JPMorgan and Plaid signed a renewed data-access agreement under which Plaid pays for consumer account data the bank had historically transmitted free (JPMorgan press release; Payments Dive; PaymentsJournal).

The load justification: JPMorgan disclosed 1.89 billion data requests from aggregators in June 2025 alone, of which only about 13 percent were tied to an immediate customer-initiated action; the remaining 87 percent were automated background pulls refreshing dashboards and transaction panels (a second pass frames the volume as roughly two billion monthly requests, up from one billion in 2023; see Fault lines). Contracted pricing is undisclosed bu