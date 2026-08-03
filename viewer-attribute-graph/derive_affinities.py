"""
Event-to-attribute derivation layer.

The core of the pipeline. Raw behavioral events are noisy, high-volume, and
useless to query directly. This layer aggregates them into durable per-viewer
attributes that a downstream consumer can actually read: genre affinity, brand
affinity, viewing summaries, and lifecycle signals. Loads the schema + raw
instance data, aggregates raw ViewingEvent
and SubscriptionEvent triples per viewer, and writes derived AffinityScore /
ViewingSummary / LifecycleSignal nodes back into the graph as new triples.

Run after generate_sample_data.py. Writes data/full_graph.ttl (schema + raw +
derived), which is what validate.py and queries.py operate on.
"""

from collections import defaultdict
from datetime import datetime

from rdflib import Graph, Literal, Namespace, RDF, XSD

SVOD = Namespace("https://github.com/Rbh2733/altdata-analytics/ontology#")
NOW = datetime(2026, 8, 1, 12, 0, 0)


def load_graph():
    g = Graph()
    g.bind("svod", SVOD)
    g.parse("ontology_schema.ttl", format="turtle")
    g.parse("data/raw_instances.ttl", format="turtle")
    return g


def title_genres(g):
    mapping = defaultdict(list)
    for t, _, gen in g.triples((None, SVOD.hasGenre, None)):
        mapping[t].append(gen)
    return mapping


def derive_genre_affinity(g, t_genres):
    """Per viewer: share of total watch-minutes attributable to each genre."""
    n_scores = 0
    for viewer, _, _ in g.triples((None, RDF.type, SVOD.Viewer)):
        minutes_by_genre = defaultdict(int)
        event_count_by_genre = defaultdict(int)
        total_minutes = 0

        for _, _, ve in g.triples((viewer, SVOD.hasViewingEvent, None)):
            duration_lits = list(g.objects(ve, SVOD.watchDurationMinutes))
            if not duration_lits:
                continue
            duration = int(duration_lits[0])
            if duration <= 0:
                continue  # invalid/messy rows excluded from the derivation, same as any real pipeline
            title = next(g.objects(ve, SVOD.viewedTitle), None)
            if title is None:
                continue
            for genre in t_genres.get(title, []):
                minutes_by_genre[genre] += duration
                event_count_by_genre[genre] += 1
                total_minutes += duration

        if total_minutes == 0:
            continue

        for i, (genre, minutes) in enumerate(sorted(minutes_by_genre.items(), key=lambda kv: -kv[1])):
            weight = round(minutes / total_minutes, 4)
            score_uri = SVOD[f"affinity_{viewer.split('#')[-1]}_genre_{i+1}"]
            g.add((score_uri, RDF.type, SVOD.AffinityScore))
            g.add((score_uri, SVOD.affinityType, Literal("genre")))
            g.add((score_uri, SVOD.forGenre, genre))
            g.add((score_uri, SVOD.affinityWeight, Literal(weight, datatype=XSD.decimal)))
            g.add((score_uri, SVOD.derivedFromEventCount, Literal(event_count_by_genre[genre], datatype=XSD.integer)))
            g.add((viewer, SVOD.hasAffinityScore, score_uri))
            n_scores += 1
    return n_scores


def derive_brand_affinity(g):
    """Per viewer: share of total watch-minutes attributable to each platform."""
    n_scores = 0
    for viewer, _, _ in g.triples((None, RDF.type, SVOD.Viewer)):
        minutes_by_platform = defaultdict(int)
        event_count_by_platform = defaultdict(int)
        total_minutes = 0

        for _, _, ve in g.triples((viewer, SVOD.hasViewingEvent, None)):
            duration_lits = list(g.objects(ve, SVOD.watchDurationMinutes))
            if not duration_lits:
                continue
            duration = int(duration_lits[0])
            if duration <= 0:
                continue
            platform = next(g.objects(ve, SVOD.onPlatform), None)
            if platform is None:
                continue
            minutes_by_platform[platform] += duration
            event_count_by_platform[platform] += 1
            total_minutes += duration

        if total_minutes == 0:
            continue

        for i, (platform, minutes) in enumerate(sorted(minutes_by_platform.items(), key=lambda kv: -kv[1])):
            weight = round(minutes / total_minutes, 4)
            score_uri = SVOD[f"affinity_{viewer.split('#')[-1]}_brand_{i+1}"]
            g.add((score_uri, RDF.type, SVOD.AffinityScore))
            g.add((score_uri, SVOD.affinityType, Literal("brand")))
            g.add((score_uri, SVOD.forPlatform, platform))
            g.add((score_uri, SVOD.affinityWeight, Literal(weight, datatype=XSD.decimal)))
            g.add((score_uri, SVOD.derivedFromEventCount, Literal(event_count_by_platform[platform], datatype=XSD.integer)))
            g.add((viewer, SVOD.hasAffinityScore, score_uri))
            n_scores += 1
    return n_scores


def derive_viewing_summary(g):
    n_summaries = 0
    for viewer, _, _ in g.triples((None, RDF.type, SVOD.Viewer)):
        total_minutes = 0
        titles_watched = set()
        minutes_by_platform = defaultdict(int)

        for _, _, ve in g.triples((viewer, SVOD.hasViewingEvent, None)):
            duration_lits = list(g.objects(ve, SVOD.watchDurationMinutes))
            if not duration_lits or int(duration_lits[0]) <= 0:
                continue
            duration = int(duration_lits[0])
            total_minutes += duration
            title = next(g.objects(ve, SVOD.viewedTitle), None)
            if title is not None:
                titles_watched.add(title)
            platform = next(g.objects(ve, SVOD.onPlatform), None)
            if platform is not None:
                minutes_by_platform[platform] += duration

        if not titles_watched:
            continue

        primary_platform = max(minutes_by_platform.items(), key=lambda kv: kv[1])[0]

        summary_uri = SVOD[f"summary_{viewer.split('#')[-1]}"]
        g.add((summary_uri, RDF.type, SVOD.ViewingSummary))
        g.add((summary_uri, SVOD.totalViewingMinutes, Literal(total_minutes, datatype=XSD.integer)))
        g.add((summary_uri, SVOD.distinctTitlesWatched, Literal(len(titles_watched), datatype=XSD.integer)))
        g.add((summary_uri, SVOD.primaryPlatform, primary_platform))
        g.add((viewer, SVOD.hasViewingSummary, summary_uri))
        n_summaries += 1
    return n_summaries


def derive_lifecycle_signal(g):
    """active / at_risk / churned, from subscription history + viewing recency."""
    n_signals = 0
    for viewer, _, _ in g.triples((None, RDF.type, SVOD.Viewer)):
        # last viewing event date
        last_watch = None
        for _, _, ve in g.triples((viewer, SVOD.hasViewingEvent, None)):
            for _, _, ts in g.triples((ve, SVOD.watchedAt, None)):
                dt = datetime.fromisoformat(str(ts))
                if last_watch is None or dt > last_watch:
                    last_watch = dt

        days_since_last_view = (NOW - last_watch).days if last_watch else 9999

        has_active_sub = (viewer, SVOD.subscribesTo, None) in g
        any_active = any(True for _ in g.triples((viewer, SVOD.subscribesTo, None)))

        if not any_active and not has_active_sub:
            stage = "churned"
        elif days_since_last_view > 60:
            stage = "at_risk"
        else:
            stage = "active"

        signal_uri = SVOD[f"lifecycle_{viewer.split('#')[-1]}"]
        g.add((signal_uri, RDF.type, SVOD.LifecycleSignal))
        g.add((signal_uri, SVOD.lifecycleStage, Literal(stage)))
        g.add((signal_uri, SVOD.daysSinceLastView, Literal(min(days_since_last_view, 9999), datatype=XSD.integer)))
        g.add((viewer, SVOD.hasLifecycleSignal, signal_uri))
        n_signals += 1
    return n_signals


def main():
    g = load_graph()
    t_genres = title_genres(g)

    before = len(g)
    n_genre = derive_genre_affinity(g, t_genres)
    n_brand = derive_brand_affinity(g)
    n_summary = derive_viewing_summary(g)
    n_lifecycle = derive_lifecycle_signal(g)
    after = len(g)

    out_path = "data/full_graph.ttl"
    g.serialize(destination=out_path, format="turtle")

    print(f"Derived {n_genre} genre-affinity scores, {n_brand} brand-affinity scores, "
          f"{n_summary} viewing summaries, {n_lifecycle} lifecycle signals.")
    print(f"Graph grew from {before} to {after} triples ({after - before} derived).")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
