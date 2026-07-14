# Pending Verification Items, Streaming Alt-Data Deep Research

> **Purpose:** Exact source locations for the three fault lines that were open in `DEEP-RESEARCH-DIFF-MAP.md` after the 2026-07-07 primary-source pass. None of these three had a usable citation inside the Deep Research docx files themselves (either no inline citation at all, or a citation to a secondary blog that isn't authoritative), so they needed an outside check rather than a within-document one. This file exists to save re-hunting through the docx text: exact file, paragraph, and quote for each claim.
> **Status: RESOLVED, 2026-07-08.** All three items closed. Reid supplied primary-source findings (Walmart's own SEC 8-K filings, Amazon's own AMC documentation, PitchBook/GetLatka company profiles), independently re-verified via direct WebSearch and a live fetch of the Amazon documentation page. All three now carry resolved fault-line entries in `DEEP-RESEARCH-DIFF-MAP.md` (Walmart Connect revenue and AMC free-tier mechanics in Section 7, Luminate headcount in Section 5). This file is kept as the source-location record, not for further action.

---

## 1. Walmart Connect revenue split (Layer 7 fault line)

Two figures, neither backed by Walmart's own IR materials.

**Location A, `07 - Deep Research - 01 - Identity, Clean Rooms, and Acquisitions.docx`**, section "Walmart Connect: Luminate Integration and Unprecedented Margin":

> "In fiscal year 2025 (ending January 31, 2025), Walmart Connect generated $4.4 billion in U.S. revenue (an increase of 24% year-over-year) and $6.4 billion globally (an increase of 46%). This growth trajectory accelerated into the first quarter of fiscal 2026, with the U.S. advertising segment expanding by 26% and global ad revenue growing by 31%..."

Repeated in a summary table later in the same file:

> Walmart Connect Advertising Metrics | FY 2025 Reported | FY 2026 / 2026 Outlook
> Global Advertising Revenue | $6.4 Billion (+46% YoY) | Q1 Growth: +31% YoY
> US Ad Revenue (Connect) | $4.4 Billion (+24% YoY) | Q1 Growth: +26% YoY

Cited to works-cited entry #6: "Walmart's Retail Media Network: How Walmart Connect Became a Profitable Growth Engine," grocerydoppio.com. Secondary blog, not Walmart's own disclosure.

**Location B, `07 - Deep Research - 02 - Identity, Clean Rooms, and Acquisitions.docx`**, section "Walled-Garden Clean Room Economics: Amazon Marketing Cloud vs. Walmart Connect (Scintilla)":

> "Walmart Connect, while smaller in absolute scale, is growing at a faster rate than Amazon's ad business, with its annual ad revenue surpassing $4.8 billion in 2025, representing a 30% year-over-year increase."

Repeated in a summary table later in the same file:

> Annual Advertising Revenue | Over $50 Billion (2026) [Amazon] | Over $4.8 Billion (2025; up 30% YoY) [Walmart Connect]

No inline citation number tied to this specific figure in what was extracted; check the file's own works-cited list for whichever numbered source sits nearest this paragraph.

**Location C, corroborating, not independent**: `04 - Deep Research - Pro - Demand & Valuation Layer.docx`, in the Luminate section, also states "In 2025, Walmart Connect generated over $4.8 billion in ad revenue," matching Location B's figure, not Location A's. This is the same underlying claim recurring, not a third independent data point.

**What's needed:** Walmart's own FY2025 10-K segment disclosure or Q4/FY2025 earnings release (Walmart's fiscal year ends January 31) for the actual reported Walmart Connect ad revenue figure, US and global split if disclosed.

---

## 2. AMC free-tier expiration terms (Layer 7 fault line)

**Location A, `07 - Deep Research - 01 - Identity, Clean Rooms, and Acquisitions.docx`**, inside a metrics table (the row immediately follows an "Average CPC (Sponsored Products)" line, suggesting a general Amazon-advertising stats table rather than a dedicated AMC pricing section):

> "AMC 1P Signal Pricing | Free to query (Effective June 1, 2026)"

No end date appears in the text captured around this line. The "through Dec 31, 2026" detail in the original diff-map draft may have been an editorial compression on my part rather than something this document actually states, worth confirming by reading the full context around this table row in the source file directly rather than trusting my summary.

**Location B, `07 - Deep Research - 02 - Identity, Clean Rooms, and Acquisitions.docx`**, section "Walled-Garden Clean Room Economics":

> "Amazon offers its core Amazon Marketing Cloud (AMC) query environment and standard advertising signals completely free of charge to any advertiser maintaining an active Amazon DSP Master Services Agreement."

No expiration stated at all, framed as an ongoing, MSA-conditioned policy rather than a time-limited promotion.

**Primary source already cited elsewhere in these docs, worth checking directly:** works-cited entry #7 in `07 - Deep Research - 01`: "Paid features overview - Amazon Ads," https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-cloud/datasources/paid_features_overview, Amazon's own documentation page, most likely to state current terms plainly.

**What's needed:** Confirm on advertising.amazon.com (or the AMC console documentation) whether the free 1P-signal access is time-limited or an ongoing MSA-based policy.

---

## 3. Luminate headcount (Layer 4 fault line)

Neither figure has an inline citation tying it to a specific source.

**Location A, `04 - Deep Research - Pro - Demand & Valuation Layer.docx`**, section "Luminate's Transmedia Scale and Clean Room Integration":

> "Led by CEO Rob Jonas, Luminate's operational scale is staggering. The company manages upward of 30 trillion data points compiled from over 500 verified global sources, employing approximately 187 professionals."

**Location B, `04 - Deep Research - FlashLite - Demand & Valuation Layer.docx`**, section "Luminate's Transmedia Registry Scale":

> "Luminate maintains a massive operational footprint, managing over 23 to 30 trillion data points compiled from 500+ verified global data partners and serving more than 1,400 institutional clients. The company operates with an estimated annual revenue in the range of $100 million to $250 million, employing a staff of 750 to 860 individuals."

Repeated in a comparison table later in the same file:

> Approximate Scale | ~$11.4M ARR; ~104 employees (as of September 2025) [Whip Media] | $100M–$250M revenue; ~750–860 employees [Luminate]

Both variants agree on CEO (Rob Jonas), parent structure (PME TopCo, a Penske Media Corporation / Eldridge Industries joint venture), and the roughly 30 trillion data points figure (Pro says "upward of 30 trillion," FlashLite says "23 to 30 trillion," close enough to not be a real conflict). The headcount figures (187 vs. 750-860) are a 4x-plus spread with no source trail in either document.

**What's needed:** Luminate's own site (luminatedata.com or similar), LinkedIn company page employee count, or a press mention with a dated headcount, none of which appear in either variant's works-cited list.

---

## Notes on method

All three items were checked against each source document's own works-cited list before concluding they need outside verification, following the same approach used to resolve the Amazon ad-revenue, LiveRamp/Publicis price, AMC lookback-window, Legend term-loan, and YipitData S-1 fault lines earlier in this review (see `DEEP-RESEARCH-DIFF-MAP.md`, Sections 1, 4, 7, and 9). Those five resolved either because a real primary source was already cited and just needed fetching, or because the "conflict" turned out to be a citation-quality problem rather than a genuine factual dispute. These three didn't have that option, the citations either don't exist or don't support the specific figure they're attached to.
