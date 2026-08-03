"""
Deterministic synthetic SVOD data generator.

Produces viewers, platforms, titles, genres, viewing events, and subscription
events as RDF instance triples conforming to ontology_schema.ttl, and writes
them to data/raw_instances.ttl. Seeded (SEED=42) so every run is identical.

Messy on purpose, same convention as the Databricks measurement notebook:
a small percentage of ViewingEvents carry an invalid (negative or missing)
watchDurationMinutes, so SHACL validation has something real to catch.
"""

import random
from datetime import datetime, timedelta

from rdflib import Graph, Literal, Namespace, RDF, XSD

SEED = 42
random.seed(SEED)

SVOD = Namespace("https://github.com/Rbh2733/altdata-analytics/ontology#")

N_VIEWERS = 60
N_TITLES = 30
VIEWING_EVENTS_PER_VIEWER = (5, 25)
MESSY_DURATION_RATE = 0.04  # ~4% of viewing events get a bad duration, on purpose

PLATFORMS = ["Netflix", "Max", "DisneyPlus", "ParamountPlus", "Peacock", "AppleTVPlus"]

GENRES = [
    "Drama", "Comedy", "SciFi", "Reality", "Documentary",
    "Crime", "Animation", "Sports", "Kids", "Horror",
]

TITLE_NAME_STEMS = [
    "Signal", "Harbor", "Verge", "Lantern", "Cascade", "Foundry", "Meridian",
    "Outpost", "Relay", "Threshold", "Compass", "Beacon", "Undertow", "Circuit",
    "Vantage", "Wren", "Ledger", "Static", "Fathom", "Ember", "Drift", "Anchorage",
    "Halcyon", "Kestrel", "Marrow", "Nocturne", "Overlook", "Passage", "Quorum", "Rift",
]


def slug(name):
    return name.replace(" ", "_").replace("'", "")


def build_reference_data(g):
    """Platforms, genres, titles (with 1-2 genres and 1-3 platform availability each)."""
    platform_uris = {}
    for p in PLATFORMS:
        uri = SVOD[f"platform_{slug(p)}"]
        g.add((uri, RDF.type, SVOD.Platform))
        g.add((uri, SVOD.name, Literal(p)))
        platform_uris[p] = uri

    genre_uris = {}
    for gname in GENRES:
        uri = SVOD[f"genre_{slug(gname)}"]
        g.add((uri, RDF.type, SVOD.Genre))
        g.add((uri, SVOD.name, Literal(gname)))
        genre_uris[gname] = uri

    title_uris = {}
    title_genres = {}
    for i in range(N_TITLES):
        tname = f"{random.choice(TITLE_NAME_STEMS)} {random.choice(['', 'II', 'III', 'Chronicles', 'Rising', '']).strip()}".strip()
        tname = f"{tname} #{i+1}"  # guarantee uniqueness
        uri = SVOD[f"title_{i+1:03d}"]
        g.add((uri, RDF.type, SVOD.Title))
        g.add((uri, SVOD.name, Literal(tname)))

        n_genres = random.choice([1, 1, 2])
        t_genres = random.sample(GENRES, n_genres)
        for gname in t_genres:
            g.add((uri, SVOD.hasGenre, genre_uris[gname]))

        n_platforms = random.choice([1, 1, 2, 3])
        t_platforms = random.sample(PLATFORMS, n_platforms)
        for pname in t_platforms:
            g.add((uri, SVOD.availableOn, platform_uris[pname]))

        title_uris[uri] = {"genres": t_genres, "platforms": t_platforms}

    return platform_uris, genre_uris, title_uris


def build_viewers(g, platform_uris, title_uris):
    viewer_uris = []
    title_list = list(title_uris.items())
    now = datetime(2026, 8, 1, 12, 0, 0)

    for i in range(N_VIEWERS):
        v_uri = SVOD[f"viewer_{i+1:03d}"]
        g.add((v_uri, RDF.type, SVOD.Viewer))
        g.add((v_uri, SVOD.name, Literal(f"Viewer {i+1:03d}")))
        viewer_uris.append(v_uri)

        # Subscription history: 1-3 platforms, each either still active or churned
        n_subs = random.choice([1, 1, 2, 3])
        sub_platforms = random.sample(PLATFORMS, n_subs)
        for j, pname in enumerate(sub_platforms):
            sub_start = now - timedelta(days=random.randint(30, 730))
            se_uri = SVOD[f"subevent_{i+1:03d}_{j+1}"]
            g.add((se_uri, RDF.type, SVOD.SubscriptionEvent))
            g.add((se_uri, SVOD.eventPlatform, platform_uris[pname]))
            g.add((se_uri, SVOD.eventType, Literal("subscribe")))
            g.add((se_uri, SVOD.eventDate, Literal(sub_start.date().isoformat(), datatype=XSD.date)))
            g.add((v_uri, SVOD.hasSubscriptionEvent, se_uri))

            churned = random.random() < 0.35
            if churned:
                churn_date = sub_start + timedelta(days=random.randint(20, 400))
                if churn_date < now:
                    ce_uri = SVOD[f"subevent_{i+1:03d}_{j+1}_churn"]
                    g.add((ce_uri, RDF.type, SVOD.SubscriptionEvent))
                    g.add((ce_uri, SVOD.eventPlatform, platform_uris[pname]))
                    g.add((ce_uri, SVOD.eventType, Literal("churn")))
                    g.add((ce_uri, SVOD.eventDate, Literal(churn_date.date().isoformat(), datatype=XSD.date)))
                    g.add((v_uri, SVOD.hasSubscriptionEvent, ce_uri))
                else:
                    churned = False
            if not churned:
                g.add((v_uri, SVOD.subscribesTo, platform_uris[pname]))

        # Viewing events: skewed toward a couple of favorite genres per viewer
        favorite_genres = set(random.sample(GENRES, random.choice([1, 2])))
        n_events = random.randint(*VIEWING_EVENTS_PER_VIEWER)
        for k in range(n_events):
            # 70% chance the pick favors the viewer's favorite genre(s)
            if random.random() < 0.7:
                candidates = [t for t, meta in title_list if set(meta["genres"]) & favorite_genres]
                if not candidates:
                    candidates = [t for t, _ in title_list]
            else:
                candidates = [t for t, _ in title_list]
            t_uri, t_meta = random.choice([(t, title_uris[t]) for t in candidates])
            watched_platform = random.choice(t_meta["platforms"])

            ve_uri = SVOD[f"viewevent_{i+1:03d}_{k+1:03d}"]
            g.add((ve_uri, RDF.type, SVOD.ViewingEvent))
            g.add((ve_uri, SVOD.viewedTitle, t_uri))
            g.add((ve_uri, SVOD.onPlatform, platform_uris[watched_platform]))

            watched_at = now - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
            g.add((ve_uri, SVOD.watchedAt, Literal(watched_at.isoformat(), datatype=XSD.dateTime)))

            # messy on purpose: ~4% of events get an invalid duration (negative),
            # so SHACL validation (validate.py) has a real violation to catch.
            if random.random() < MESSY_DURATION_RATE:
                duration = -random.randint(1, 30)
            else:
                duration = random.randint(5, 140)
            g.add((ve_uri, SVOD.watchDurationMinutes, Literal(duration, datatype=XSD.integer)))

            g.add((v_uri, SVOD.hasViewingEvent, ve_uri))

    return viewer_uris


def main():
    g = Graph()
    g.bind("svod", SVOD)

    platform_uris, genre_uris, title_uris = build_reference_data(g)
    viewer_uris = build_viewers(g, platform_uris, title_uris)

    out_path = "data/raw_instances.ttl"
    g.serialize(destination=out_path, format="turtle")

    print(f"Generated {len(viewer_uris)} viewers, {len(PLATFORMS)} platforms, "
          f"{len(title_uris)} titles, {len(GENRES)} genres.")
    print(f"Total triples: {len(g)}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
