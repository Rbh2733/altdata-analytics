"""Optional live adapter, same interface as tagger_mock.tag_titles().

Batched strict JSON against the Claude API. Because a schema cannot
enforce row coverage, this adapter verifies every batch covers every
sent row exactly once and fails loudly on a mismatch instead of letting
a dropped row silently corrupt the merge. Gated on ANTHROPIC_API_KEY: an
absent key fails loudly, it never silently falls back to the mock.
"""

import json
import os

from estimation.tagger_mock import FUNCTIONS

BATCH_SIZE = 25
MODEL = "claude-opus-4-8"

_SYSTEM = (
    "Classify each job title into exactly one function: engineering, "
    "ml_infrastructure, research, sales, support, or other. "
    "ml_infrastructure covers ML/AI infrastructure, GPU/cluster, and "
    "datacenter operations roles; research covers scientist and "
    "researcher roles. Respond with a JSON array of objects "
    "{\"id\": <int>, \"function\": <one of the six>}, one object per "
    "input row, in the same order, covering every id exactly once. "
    "No prose, JSON only."
)


def _get_client():
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError(
            "tagger_claude requires the 'anthropic' package; install it "
            "or run with the default mock tagger") from e
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set; tagger_claude fails loudly "
            "rather than silently falling back to the mock tagger")
    return anthropic.Anthropic(api_key=key)


def _classify_batch(client, titles_with_ids):
    payload = json.dumps([{"id": i, "title": t} for i, t in titles_with_ids])
    resp = client.messages.create(
        model=MODEL, max_tokens=2000, system=_SYSTEM,
        messages=[{"role": "user", "content": payload}],
    )
    text = "".join(block.text for block in resp.content if hasattr(block, "text"))
    parsed = json.loads(text)
    by_id = {}
    for row in parsed:
        rid = row["id"]
        func = row["function"]
        if func not in FUNCTIONS:
            raise RuntimeError(f"tagger_claude returned an invalid function {func!r} "
                                f"for row {rid}")
        by_id[rid] = func
    sent_ids = {i for i, _ in titles_with_ids}
    missing = sent_ids - set(by_id.keys())
    if missing:
        raise RuntimeError(
            f"tagger_claude dropped {len(missing)} row(s) from a batch of "
            f"{len(titles_with_ids)}: ids {sorted(missing)[:5]}...; failing "
            "loudly rather than letting a dropped row corrupt the merge")
    return by_id


def tag_titles(titles) -> list:
    client = _get_client()
    titles = list(titles)
    results = {}
    for start in range(0, len(titles), BATCH_SIZE):
        chunk = list(enumerate(titles))[start:start + BATCH_SIZE]
        results.update(_classify_batch(client, chunk))
    return [results[i] for i in range(len(titles))]
