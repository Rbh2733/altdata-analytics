# viewer-attribute-graph

Turning raw streaming behavior into durable, queryable viewer attributes, with
schema validation that catches bad data before anything downstream reads it.

Raw viewing and subscription events are high-volume and close to useless to
query directly. Nobody asks "list every play event for viewer 41." They ask
what that viewer is into, which platform holds their attention, and whether
they are about to leave. This pipeline does that translation, stores the result
as a graph so the derived attributes stay attached to a single canonical viewer,
and validates the whole thing against a schema before it is trusted.

Implemented in RDF and OWL with SPARQL for reads and SHACL for validation,
because a graph is the honest shape for this data. Every derived attribute has
to point back at one viewer across three different event types that share no
natural key, which is a join problem before it is a storage problem.

---

## What it does, end to end

1. **Generate.** A deterministic synthetic dataset of 60 viewers, 6 platforms,
   30 titles, and 10 genres, plus their viewing and subscription events. Seeded
   (`SEED=42`), so every run reproduces exactly.
2. **Derive.** Raw `ViewingEvent` and `SubscriptionEvent` triples are aggregated
   per viewer into four durable attribute types, written back into the graph as
   new nodes.
   - **Genre affinity**, share of watch-minutes per genre, ranked, carrying its
     own provenance (the source event count behind each score)
   - **Brand affinity**, the same operation per platform
   - **Viewing summary**, total minutes, distinct titles, primary platform
   - **Lifecycle signal**, active / at_risk / churned, from subscription history
     plus days since last view
3. **Validate.** SHACL shapes run over the derived graph and report every
   violation with its subject, path, and constraint.
4. **Query.** Five SPARQL reads answering the questions the attributes exist for.

```bash
pip install -r requirements.txt
python run_all.py
```

Each step also runs standalone (`generate_sample_data.py`, `derive_affinities.py`,
`validate.py`, `queries.py`).

---

## The entity-resolution part, which is the actual hard part

`ViewingEvent`, `SubscriptionEvent`, and every derived `AffinityScore` resolve
back to one canonical `Viewer` URI. That is what makes a query like "show me
at-risk viewers joined to their top genre" a single traversal instead of a
three-way reconciliation. The graph does not fix the identity problem, it just
makes the fix legible once you have done it, and doing it is the work.

---

## The data is synthetic, and it is messy on purpose

`generate_sample_data.py` builds the whole world from a fixed seed. **Roughly 4
percent of ViewingEvents carry an invalid negative watch duration**, planted
deliberately, so the validator has something real to catch. A validation layer
that reports a clean pass over clean data proves nothing.

The derivation layer excludes those rows before aggregating, so every derived
attribute is clean even though the raw graph is not. That split is the point.
Validation reports on the raw truth; derivation defends the outputs.

---

## What a clean run produces

```
Generated 60 viewers, 6 platforms, 30 titles, 10 genres.
Total triples: 6020
Wrote data/raw_instances.ttl

Derived 342 genre-affinity scores, 279 brand-affinity scores,
60 viewing summaries, 60 lifecycle signals.
Graph grew from 6123 to 10389 triples (4266 derived).
Wrote data/full_graph.ttl

Conforms: False
Violations reported: 24
  (all 24 are the seeded negative-duration ViewingEvents, correctly caught by
  ViewingEventShape's sh:minInclusive constraint)

=== Q1: Top genre affinity per viewer ===
  Viewer 013 | Documentary | 0.9698 | 4
  Viewer 041 | Horror      | 0.8453 | 10
  ...

=== Q3: At-risk / churned viewers, joined to top genre affinity ===
  Viewer 055 | at_risk | 173 days | Drama  | 0.5366
  Viewer 023 | churned | 163 days | Comedy | 0.3972
  ...
```

The two triple counts are different numbers on purpose. 6020 is the instance
data alone. 6123 is that data with the schema loaded on top of it, which is what
the derivation step reads.

---

## Scope, stated plainly

**9 classes.** Viewer, Platform, Title, Genre, ViewingEvent, SubscriptionEvent,
AffinityScore, ViewingSummary, LifecycleSignal.

**26 properties**, 14 object and 12 datatype, with domains and ranges declared.

**6 SHACL NodeShapes**, one per validated class (Viewer, ViewingEvent,
SubscriptionEvent, Title, AffinityScore, LifecycleSignal).

**5 SPARQL 1.1 queries**, covering aggregation, grouped subqueries, multi-hop
traversal, and filtering.

**What this is not.** It runs in rdflib against a local graph, not a hosted
triplestore, and not at production volume. It demonstrates the notation and the
underlying operation on a dataset small enough to verify by hand. Treat it as a
worked example, not as evidence of scale.

---

## Files

| File | Purpose |
|---|---|
| `ontology_schema.ttl` | RDFS/OWL schema, classes, properties, domains and ranges |
| `generate_sample_data.py` | Deterministic generator, writes `data/raw_instances.ttl` |
| `derive_affinities.py` | Event-to-attribute derivation, writes `data/full_graph.ttl` |
| `shapes.ttl` | SHACL NodeShapes |
| `validate.py` | Runs pySHACL, prints the conformance report |
| `queries.py` | Five SPARQL reads over the derived graph |
| `run_all.py` | Single-command end-to-end run |

Committed outputs in `data/` regenerate byte-identically from a clean clone.
