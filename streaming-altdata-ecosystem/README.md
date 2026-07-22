# Streaming Alt-Data Ecosystem Map

A research map of the layers that sit between raw consumer behavior and investor-grade measurement in streaming media, and the companies operating at each layer. The premise the whole map hangs on: streaming platforms and Big Tech gatekeepers increasingly withhold granular subscriber, viewership, and engagement data, so studios, advertisers, and analysts pay a stack of specialized vendors to reconstruct ground truth. The map records where each layer sits, what it does, who its customers are, and what is currently threatening it. It documents market structure; it does not make recommendations.

## How it was built

The map synthesizes more than twenty AI deep-research passes run against a common brief, cross-checked against each other and, where flagged in the text, against primary sources: SEC filings, earnings releases, court dockets, and company documentation. Where two credible passes disagreed and no primary source settled it, the disagreement is recorded in place as an open fault line rather than silently resolved. Provenance notes at the end of each layer file reference a source-document archive and a pass-by-pass comparison file that are part of the private working tree, not this repository.

## The documents

- `streaming-altdata-ecosystem.md`: the overview map. The eight-layer taxonomy, cross-cutting mechanics (synthetic proxy construction, cross-layer triangulation, the dual posture of the gatekeepers), consolidation events, regulatory fronts, and the fault lines left open.
- `company-roster.md`: a flat reference list, one line per company, organized by the same eight layers.
- `layers/`: one findings file per layer.
  - `00-gatekeeper-layer.md`: the platforms whose withheld data and rights control generate demand for every vendor layer below.
  - `01-wallet-layer.md`: subscriber transaction intelligence: card and bank panels, cohort survival, plan-mix migration, and the bank API tolling and deletion-law pressure on the model.
  - `02-glass-layer.md`: smart-TV automatic content recognition and the TV measurement currency war.
  - `03-shield-layer.md`: media quality verification and the connected-TV fraud arms race.
  - `04-demand-valuation-layer.md`: synthetic demand indices and how they price content and talent.
  - `05-funnel-layer.md`: discovery, watchlist, and app-store intent as leading indicators of subscriber momentum.
  - `06-sports-rights-layer.md`: the league data triopoly and betting-data economics.
  - `07-identity-clean-rooms-layer.md`: the identity and clean-room substrate everything else matches through, and the ownership change that ended its neutrality.
- `layers/Focus Research/`: eight focused follow-up files, one per layer, each commissioned against specific gaps the first pass left open, with an explicit verdict on which gaps closed and which remain.

## As of

This is a point-in-time research map. The documents were written between July 6 and July 14, 2026, and the deal statuses, litigation postures, prices, and headcounts in them are current only to that window. Anything decision-relevant should be re-verified against primary sources before reuse.
