# Streaming Alt-Data Ecosystem: Company Roster

> Flat reference list, one line per company, organized by the same eight layers as `streaming-altdata-ecosystem.md`. Purpose: a lookup for scoping deep research passes. Not a scoring document, no ratings, no verdicts.

---

## Wallet Layer

| Company | What it does |
|---|---|
| YipitData | Broad multi-sector alt-data incumbent; Carlyle-backed; absorbed 1010data (2023); reportedly eyeing a 2026-2027 IPO or exit |
| Consumer Edge | Multi-sector consolidator; acquired Earnest Analytics (Apr 2025), fusing transaction data with healthcare/pharmacy claims |
| Antenna | Streaming-specific specialist; BDMI/Raine Ventures-backed; serial-churner tracking and the ACR-plus-transaction "Subscriber Views" product |
| Bloomberg Second Measure | Multi-sector receipt-panel peer to YipitData |
| M Science | Quant-focused; raw, unaggregated algorithmic feeds built for hedge-fund ingestion |

## Glass Layer (includes Attention Verification)

| Company | What it does |
|---|---|
| Nielsen | Legacy national TV-currency incumbent (~80-90% share); mid-crisis on accreditation and methodology since 2021 |
| Comscore (Nasdaq: SCOR) | Public micro-cap challenger currency; recapitalized 2025-2026; has its own `companies/Comscore/` folder |
| VideoAmp | JIC-certified currency challenger; cross-platform planner (VXP); scaling upfront deal volume |
| iSpot.tv | JIC-certified challenger; integrated into Paramount and AMC Networks upfront guarantees |
| Samba TV | Chipset-level ACR, independent of any single TV brand |
| Vizio Inscape | ACR data unit; Vizio itself was acquired by Walmart in 2024, ownership/independence of Inscape as a standalone data product needs re-confirming |
| EDO Inc. | Attention verification; links CTV ad exposure to downstream digital outcomes |
| TVision | Attention verification; infrared-sensor household panels measuring actual eyes-on-screen |

## Shield Layer

| Company | What it does |
|---|---|
| DoubleVerify (NYSE: DV) | Sole remaining public Shield-layer proxy; CTV fraud/brand-safety verification |
| Integral Ad Science | DV's former public duopoly peer; taken private by Novacap (Dec 2025, ~$1.9B) |

## Demand/Valuation Layer

| Company | What it does |
|---|---|
| Parrot Analytics | Demand-expression index; cost-per-demand-point metric; the *Suits* licensing case study |
| Ampere Analysis | European demand-forecasting firm; acquired PlumResearch (May 2026) |
| PlumResearch | Device-agnostic tracking and behavioral metrics; now part of Ampere Analysis |
| Gracenote | Nielsen subsidiary; supplies metadata/content ontology rather than competing on demand directly |
| Whip Media (TV Time shut down) | Consumer app TV Time shut down Jul 15, 2026; owner Blue Torch Capital pivoted resources to Helix, an enterprise B2B SaaS platform. Bingers, launched by TV Time's original founder, is an unaffiliated indie successor, not a Whip Media product; see `layers/04-demand-valuation-layer.md` |
| Luminate | Demand/behavior analytics; also powers Walmart Connect's clean room (Identity layer) |
| Diesel Labs | Content analytics and audience-preference mapping; owned by Forma Group; launched Diesel AI ("Daisy", Jul 2024) and PanelAI synthetic focus groups; see `layers/04-demand-valuation-layer.md` |

## Funnel Layer

| Company | What it does |
|---|---|
| JustWatch | Content discovery and search-navigation aggregator |
| Reelgood | Content discovery and search-navigation aggregator |
| Sensor Tower | App-store analytics; used as a CAC-efficiency proxy tool |

## Sports-Rights Layer

| Company | What it does |
|---|---|
| Stats Perform | FIFA's official betting-data and live-stream distributor (2026 Men's/2027 Women's World Cup); Opta and RunningBall infrastructure |
| Sports Innovation Lab | "Fluid Fan Graph" transactional fan-behavior data; acquired by Genius Sports (Sep 2025) |
| Zoomph | Real-time social audience intelligence; partnered with Sports Innovation Lab (Apr 2025), a partnership whose endgame was the Genius Sports acquisition |
| Genius Sports (NYSE: GENI) | Public sports-data vendor; NFL exclusive data distribution through 2029 with the league its largest shareholder (~8.7%); NCAA through 2032; acquired Sports Innovation Lab (Sep 2025) and Legend (Apr 2026); see `layers/06-sports-rights-layer.md` |
| Sportradar (Nasdaq: SRAD) | Public sports-data vendor; NBA (through 2030-31 per the research passes), MLB (through 2032, with league equity), NHL, UEFA, Bundesliga; acquired IMG ARENA (Nov 2025); Kalshi deal (Jun 2026); see `layers/06-sports-rights-layer.md` |

## Identity Resolution & Clean Rooms Layer

| Company | What it does |
|---|---|
| LiveRamp | Primary independent identity toll booth (RampID); being acquired by Publicis Groupe (announced May 2026, ~$2.17B EV) |
| The Trade Desk | Owns Unified ID 2.0 (UID2), the leading open-source identity alternative to LiveRamp |
| Amazon Marketing Cloud | Amazon's walled-garden clean room |
| Walmart Connect | Walmart's walled-garden clean room, powered by Luminate (rebranding to Scintilla); global ad revenue $4.4B in FY2025 and $6.4B in FY2026 per Walmart's SEC 8-Ks |

---

## Layer 0 - Ecosystem Gatekeepers

Surrounds the ecosystem as the reason it exists. Where data and money flow down from in different forms.

| Company | Role |
|---|---|
| Amazon | Blends standalone streaming economics into "Subscription Services"; dual posture (withholds from studios, sells to advertisers via AMC) |
| Apple | Blends Apple TV+ into "Services"; no disclosed standalone ARPU or churn |
| Roku | Dual posture via the Roku Data Cloud clean room (legacy OneView retired), same withhold-and-monetize pattern as Amazon; being acquired by Fox under a definitive agreement (June 15, 2026, ~$22B EV, close expected H1 2027); see `layers/00-gatekeeper-layer.md` |
| Fox | Ad-dependent Linear Yield Company (Reid's taxonomy, "Live Event Focus"); Fox One premium pricing plus the definitive agreement to acquire Roku (June 15, 2026) make it a gatekeeper spanning rights supply and, post-close, owned distribution and hardware telemetry |
| Netflix | Historically operated outside this vendor ecosystem on first-party telemetry; practices the licensing-arbitrage pattern described as the Netflix Paradox; ad-tier scaling, an in-house ad server, and clean-room partnerships have converged it with Amazon and Roku, and the old outside-the-ecosystem framing is now historical |
| Google/YouTube | YouTube TV (~8M subs) + Sunday Ticket; demonstrated real carriage-dispute leverage over Disney (Nov 2025, ESPN/ABC/FX pulled ~2 weeks, Google held firm); captures more total US TV time than any other platform |
| Disney | Content Fortress vertically integrating sports distribution (ESPN Unlimited, Fubo acquisition, Fox One bundle, NFL's 10% ESPN equity stake); gatekeeper via bundling/rights-equity opacity, not data-withholding |
| Paramount Skydance/WBD | Reclassified by the layer's deep-research pass as a vendor subject, not a gatekeeper (`layers/00-gatekeeper-layer.md`); ~$79B combined debt, US NBA rights conceded to Disney/ESPN, Amazon, and NBCUniversal; the active gatekeeper set is effectively seven |
