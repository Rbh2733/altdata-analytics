"""
Single-command reproducibility: regenerate data, derive attributes, validate,
and query, end to end. Mirrors the "Run All" cell pattern from the sibling
Databricks measurement notebook.
"""

import subprocess
import sys

STEPS = [
    ("Generating synthetic instance data", ["python", "generate_sample_data.py"]),
    ("Deriving affinity / summary / lifecycle attributes", ["python", "derive_affinities.py"]),
    ("Validating the derived graph against SHACL shapes", ["python", "validate.py"]),
    ("Running the SPARQL query suite", ["python", "queries.py"]),
]


def main():
    for title, cmd in STEPS:
        print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Step failed: {' '.join(cmd)}")
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
