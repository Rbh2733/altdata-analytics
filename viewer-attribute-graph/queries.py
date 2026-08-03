"""
SPARQL queries against the derived graph (data/full_graph.ttl). Five reads
covering the questions the derived attributes exist to answer: genre affinity,
brand affinity, cross-platform graph traversal, and lifecycle/churn signals
joined back to genre affinity.

The last of those is also the entity-resolution demonstration. ViewingEvent,
SubscriptionEvent, and AffinityScore all resolve back to one canonical URI per
viewer, so a single node answers every query below. That resolution is the
thing that makes the graph queryable at all, and it is the same problem as
joining two systems that share no key.
"""

from rdflib import Graph

DATA_GRAPH = "data/full_graph.ttl"

Q1_TOP_GENRE_AFFINITY = """
PREFIX svod: <https://github.com/Rbh2733/altdata-analytics/ontology#>
SELECT ?viewerName ?genreName ?weight ?eventCount
WHERE {
    ?viewer a svod:Viewer ; svod:name ?viewerName ; svod:hasAffinityScore ?score .
    ?score svod:affinityType "genre" ; svod:forGenre ?genre ; svod:affinityWeight ?weight ;
           svod:derivedFromEventCount ?eventCount .
    ?genre svod:name ?genreName .
}
ORDER BY DESC(?weight)
LIMIT 10
"""

Q2_BRAND_AFFINITY = """
PREFIX svod: <https://github.com/Rbh2733/altdata-analytics/ontology#>
SELECT ?viewerName ?platformName ?weight
WHERE {
    ?viewer a svod:Viewer ; svod:name ?viewerName ; svod:hasAffinityScore ?score .
    ?score svod:affinityType "brand" ; svod:forPlatform ?platform ; svod:affinityWeight ?weight .
    ?platform svod:name ?platformName .
}
ORDER BY DESC(?weight)
LIMIT 10
"""

Q3_AT_RISK_VIEWERS = """
PREFIX svod: <https://github.com/Rbh2733/altdata-analytics/ontology#>
SELECT ?viewerName ?stage ?daysSinceView ?topGenre ?topWeight
WHERE {
    ?viewer a svod:Viewer ; svod:name ?viewerName ; svod:hasLifecycleSignal ?signal .
    ?signal svod:lifecycleStage ?stage ; svod:daysSinceLastView ?daysSinceView .
    FILTER(?stage IN ("at_risk", "churned"))
    {
        SELECT ?viewer (MAX(?w) AS ?topWeight)
        WHERE {
            ?viewer svod:hasAffinityScore ?s .
            ?s svod:affinityType "genre" ; svod:affinityWeight ?w .
        }
        GROUP BY ?viewer
    }
    ?viewer svod:hasAffinityScore ?topScore .
    ?topScore svod:affinityType "genre" ; svod:affinityWeight ?topWeight ; svod:forGenre ?genreUri .
    ?genreUri svod:name ?topGenre .
}
ORDER BY DESC(?daysSinceView)
LIMIT 10
"""

Q4_CROSS_PLATFORM_TITLES = """
PREFIX svod: <https://github.com/Rbh2733/altdata-analytics/ontology#>
SELECT ?titleName (COUNT(?platform) AS ?platformCount)
WHERE {
    ?title a svod:Title ; svod:name ?titleName ; svod:availableOn ?platform .
}
GROUP BY ?titleName
HAVING (COUNT(?platform) > 1)
ORDER BY DESC(?platformCount)
LIMIT 10
"""

Q5_GENRE_POPULARITY = """
PREFIX svod: <https://github.com/Rbh2733/altdata-analytics/ontology#>
SELECT ?genreName (SUM(?duration) AS ?totalMinutes) (COUNT(?event) AS ?eventCount)
WHERE {
    ?event a svod:ViewingEvent ; svod:viewedTitle ?title ; svod:watchDurationMinutes ?duration .
    FILTER(?duration > 0)
    ?title svod:hasGenre ?genre .
    ?genre svod:name ?genreName .
}
GROUP BY ?genreName
ORDER BY DESC(?totalMinutes)
"""


def run(g, label, query, limit_rows=8):
    print(f"\n=== {label} ===")
    results = list(g.query(query))
    for row in results[:limit_rows]:
        print("  " + " | ".join(str(v) for v in row))
    if len(results) > limit_rows:
        print(f"  ... ({len(results) - limit_rows} more rows)")
    print(f"  ({len(results)} row(s) total)")


def main():
    g = Graph().parse(DATA_GRAPH, format="turtle")
    print(f"Loaded {len(g)} triples from {DATA_GRAPH}")

    run(g, "Q1: Top genre affinity per viewer (event-to-ontology derivation)", Q1_TOP_GENRE_AFFINITY)
    run(g, "Q2: Brand/platform affinity per viewer", Q2_BRAND_AFFINITY)
    run(g, "Q3: At-risk / churned viewers, joined to their top genre affinity", Q3_AT_RISK_VIEWERS)
    run(g, "Q4: Titles available on more than one platform (graph traversal)", Q4_CROSS_PLATFORM_TITLES)
    run(g, "Q5: Genre-level viewing popularity across the whole graph", Q5_GENRE_POPULARITY)


if __name__ == "__main__":
    main()
