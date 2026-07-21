"""Live LLM tagger: classifies the unmatched tail with the Claude API.

Same interface as tagger_mock.tag(rows, vendors). Requires the anthropic
package and an ANTHROPIC_API_KEY (or an `ant auth login` profile) in the
environment. Strings are sent in batches with a strict JSON schema so the
response parses without cleanup; anything the model cannot place against
the provided vendor list comes back as a new-vendor candidate.

Run selection lives in run_all.py (--tagger claude). The default path uses
the deterministic mock so the published numbers stay reproducible.
"""

import json

import anthropic

MODEL = "claude-opus-4-8"
BATCH = 25

SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "raw_id": {"type": "string"},
                    "vendor_guess": {"type": "string"},
                    "category_guess": {"type": "string"},
                    "confidence": {"type": "number"},
                    "new_vendor_flag": {"type": "integer"},
                },
                "required": ["raw_id", "vendor_guess", "category_guess",
                             "confidence", "new_vendor_flag"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def tag(rows, vendors):
    client = anthropic.Anthropic()
    vendor_list = "\n".join(f"- {v['vendor']} ({v['category']})" for v in vendors)
    categories = sorted({v["category"] for v in vendors})
    out = []
    for start in range(0, len(rows), BATCH):
        chunk = rows[start:start + BATCH]
        lines = "\n".join(f"{r['raw_id']}: {r['raw_string']}" for r in chunk)
        prompt = (
            "You are resolving raw card-feed merchant strings to a canonical "
            "vendor table.\n\nCanonical vendors:\n" + vendor_list +
            "\n\nValid categories: " + ", ".join(categories) +
            "\n\nFor each string below, either match it to one canonical vendor "
            "(vendor_guess = exact canonical name, new_vendor_flag = 0) or, if "
            "it is not any vendor in the table, set vendor_guess to an empty "
            "string, new_vendor_flag = 1, and pick the most plausible category. "
            "Confidence is 0 to 1. Do not force a match.\n\nStrings:\n" + lines
        )
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason != "end_turn":
            raise RuntimeError(
                f"tagger batch at {start} stopped with {response.stop_reason}"
            )
        block = next((b for b in response.content if b.type == "text"), None)
        if block is None:
            raise RuntimeError(f"tagger batch at {start} returned no text block")
        results = json.loads(block.text)["results"]
        # the schema cannot enforce row coverage, so verify it before trusting
        # the batch; a dropped or mangled raw_id must fail loudly, not merge
        expected = {r["raw_id"] for r in chunk}
        got = [item["raw_id"] for item in results]
        if set(got) != expected or len(got) != len(expected):
            raise ValueError(
                f"tagger batch at {start}: expected {len(expected)} rows, "
                f"got {len(got)} covering {len(set(got))} ids"
            )
        out.extend(results)
    return out
