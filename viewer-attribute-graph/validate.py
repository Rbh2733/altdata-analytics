"""
Post-load SHACL validation, run against the derived graph (data/full_graph.ttl)
using shapes.ttl. Prints a conformance summary and the individual violations
found.

The seeded messy rows in generate_sample_data.py (negative watchDurationMinutes
on ~4% of ViewingEvents) are expected to fail ViewingEventShape. That is the
point: a validator with nothing to catch proves nothing.
"""

from rdflib import Graph
from pyshacl import validate

DATA_GRAPH = "data/full_graph.ttl"
SHAPES_GRAPH = "shapes.ttl"


def main():
    data_graph = Graph().parse(DATA_GRAPH, format="turtle")
    shapes_graph = Graph().parse(SHAPES_GRAPH, format="turtle")

    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
    )

    violation_count = results_text.count("Constraint Violation")

    print(f"Conforms: {conforms}")
    print(f"Violations reported: {violation_count}")
    print("-" * 70)
    print(results_text)


if __name__ == "__main__":
    main()
