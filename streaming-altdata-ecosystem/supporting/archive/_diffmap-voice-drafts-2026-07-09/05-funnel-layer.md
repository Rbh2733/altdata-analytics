# Layer 5: Funnel (Downstream Intent & Discovery) (Master Findings)

> **Document type:** Master findings file, the merged research record for this layer. Not a prompt file, not the diff map.
> **Created:** 2026-07-09, rebuilt directly from the source documents, superseding the 2026-07-08 spec-style draft (which restated merge logic without the research content; archived at `supporting/archive/_superseded-layer-specs-2026-07-08/05-funnel-layer.md`).
> **Sources:** two Gemini Deep Research passes, Pro (original) and Flash (added 2026-07-08). Both-and merge with no base document: the two variants are complementary rather than competing and carry equal standing throughout.
> **Readiness note:** the prompt file flagged this layer as the one most likely to come back thin, given it had the thinnest existing base in the project. Neither pass came back thin; both delivered against all five objectives.

---

## What this layer measures

The Funnel layer sits at the top of the streaming conversion funnel, upstream of every transaction. It tracks the behavioral precursors to subscriber acquisition: search navigation, watchlist additions, application-store download velocity, and platform click-through rates, all captured before any billing relationship exists. Its analytical value peaks during tentpole-title launch windows, when platforms run aggressive performance-marketing bursts and bid up mobile and connected-TV advertising inventory to drive app downloads; by tracking upstream intent against that ad spend, analysts can reverse-engineer a platform's customer acquisition cost efficiency well before quarterly disclosure. The layer has historically been the least documented segment of the streaming alt-data map, largely because its vendors present as consumer utilities while their actual enterprise architectures are B2B data licensing and advertising engines.

---

## 1. Ownership and scale (Objective 1)

### JustWatch

JustWatch GmbH was founded August 14, 2014 in Berlin by David Croyé, Christoph Hoyer, Kevin Hiller, Dominik Raute, Ingke Purrmann, and Michael Wilken (Wikipedia, Tracxn). Croyé had been Chief Marketing Officer at kaufDA, sold to Axel Springer for roughly $40 million in March 2011, and recycled personal proceeds from that exit into JustWatch's initial funding (JustWatch "Our Story," Startuprad). The initial bootstrap totaled roughly $2.5 million: about $500,000 of founder capital plus roughly $2 million in public innovation grants and private loans. The company launched in the US and Germany in February 2015 and reached profitability within its first year.

External capital has been deliberately minimal. In 2017, after breakeven, JustWatch took an undisclosed seed round led by Cologne-based STS Ventures (Stephan Schubert's "camel" capital-efficiency philosophy: survive funding winters, high unit contribution margins, no vanity metrics) alongside Christian Gaiser and a consortium of roughly eight angel investors; the founders retain majority voting control (STS Ventures, Startuprad). In December 2018 the company received a €223,544 (about $253,000) EU grant, structured as prize money, allocated to database infrastructure and the visibility of European film and television works (North Data, PitchBook). In December 2019 JustWatch used internal cash flow to acquire its New York rival GoWatchIt from Plexus Entertainment, absorbing a competitor and establishing a North American operational beachhead without dilutive financing.

Scale as of the 2024-2026 window: over 40 million monthly active users by late 2023, growing past 50 million monthly streamers (estimates run as high as 60 million) across 139-140 countries (Tracxn, LeadIQ). The backend indexes over 470,000 film and TV titles across more than 1,100 streaming services. Headcount grew from 56 employees in 2020 to a range of 200-243 by 2026, spanning 46 nationalities across a distributed office network covering Berlin, Los Angeles, New York, London, Paris, Rome, Madrid, Munich, and Dubai. Revenue: a 2026 point estimate of roughly $68 million (Kona Equity) sits inside a credible $50 million to $100 million range built from recruitment telemetry and specialized financial intelligence platforms; the company is private with no public filings, so all revenue figures are analyst estimates. The higher end of the range is consistent with the scale of its programmatic media buying arm, which manages entertainment advertising budgets across more than 100 markets.

### Reelgood

Reelgood was founded in 2015 in San Francisco by David Sanderson, built to solve streaming fragmentation with a unified cross-service search engine and guide (Tracxn, PitchBook). Total capital raised runs $13.3 million to $15.4 million depending on whether the debt facility is counted, itemized as follows (PitchBook, Startup Intros, VCBacked):

- April 2015: $1 million seed led by Harrison Metal.
- November 2016: $3 million extended seed with 8VC, Accel, Acrew Capital, Lerer Hippeau, and Slow Ventures.
- July 2017: $3.5 million venture round led by August Capital, with Harrison Metal and Social Capital.
- December 2019: $6.75-6.8 million Series A led by Runa Capital, with August Capital continuing.
- March 2022: $4.1 million structured debt facility, a runway-extension mechanism avoiding further equity dilution.

In October 2018 Reelgood acquired rival metadata supplier Guidebox, internalizing its data supply chain after concluding that legacy metadata providers (including Nielsen's Gracenote) delivered only 60-70% accuracy on real-time streaming availability (PitchBook). The consumer app's roughly 10 million users supply behavioral training data for its proprietary AI-driven metadata matching engine, the company's primary enterprise asset. The platform tracks over 4 million individual titles across more than 300 streaming services in 25-plus international markets.

Reelgood runs lean: headcount estimates span 27 to 60 employees through the 2024-2026 period (the overlapping 27-43 and 30-60 ranges are estimate variance, not conflict). Revenue estimates run $5.8 million to $11.1 million annually (Kona Equity at the low end), with annual recurring revenue pegged around $8.4 million and revenue per employee around $196,000 (Growjo). Its strategic weight exceeds its revenue: enterprise clients across hardware, search, and finance depend structurally on its availability API.

### Sensor Tower

Sensor Tower was founded in 2013 in San Francisco by Oliver Yeh and Alex Malafeev, incubated through AngelPad. Its seed round was $1 million in August 2013, led by Rembrandt Venture Partners; this figure was independently confirmed against AngelPad's own blog during the consolidation review. The founders ran a profit-first, bootstrapped model for the first five to seven years, retaining over 70% voting control through year five with minimal dilution.

The capital-structure inflection came in May 2020, when Riverwood Capital injected $45 million of Series B growth equity (Riverwood Capital), converting a founder-controlled startup into an institutionally backed scale-up. By 2023 the cap table spanned founders, Riverwood, and an expanded employee stock ownership plan. The transformation completed in March 2024 with the acquisition of primary rival data.ai (formerly App Annie, which had raised $157 million in venture capital), for an undisclosed sum (PR Newswire, GamesIndustry.biz). The deal was financed by a debt-and-equity syndicate led by Bain Capital Credit, with follow-on participation from Riverwood Capital and Paramark Ventures. Governance shifted decisively to private equity stewardship: Riverwood's Francisco Alvarez-Demalde chair