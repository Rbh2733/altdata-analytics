"""Committed artifacts exist, parse, and contain none of the banned
content (dash characters, emoji, trading vocabulary, private strings)."""

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

OUTPUTS = ["estimates.csv", "scorecard.csv", "scorecard.md", "qa_report.md",
           "sql_report.md", "metrics.json"]

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv"}

# Banned words are assembled from characters so this file passes its own
# scan. Word-boundary matching keeps ordinary words like "buyers" legal.
BANNED_WORDS = ["".join(w) for w in (
    ("b", "u", "y"), ("s", "e", "l", "l"), ("l", "o", "n", "g"),
    ("s", "h", "o", "r", "t"), ("e", "n", "t", "r", "y"),
    ("e", "x", "i", "t"), ("a", "l", "p", "h", "a"),
    ("c", "o", "n", "v", "i", "c", "t", "i", "o", "n"),
)]
BANNED_PHRASES = ["".join(p) for p in (
    ("p", "r", "i", "c", "e", " ", "t", "a", "r", "g", "e", "t"),
    ("s", "t", "o", "p", " ", "l", "o", "s", "s"),
)]
BANNED_SUBSTRINGS = ["".join(s) for s in (
    ("y", "i", "p", "i", "t"), ("r", "e", "i", "d", "n", "_"),
)]

EM_DASH = b"\xe2\x80\x94"
EN_DASH = b"\xe2\x80\x93"


def _all_files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def test_all_expected_outputs_exist_parse_nonempty():
    for name in OUTPUTS:
        p = ROOT / "outputs" / name
        assert p.exists() and p.stat().st_size > 0, name
    est = pd.read_csv(ROOT / "outputs" / "estimates.csv")
    assert len(est) == 4 * 6 * 12 * 6
    sc = pd.read_csv(ROOT / "outputs" / "scorecard.csv")
    assert len(sc) > 0
    json.loads((ROOT / "outputs" / "metrics.json").read_text(encoding="utf-8"))


def test_no_banned_characters_anywhere():
    for p in _all_files():
        blob = p.read_bytes()
        assert EM_DASH not in blob, f"em dash in {p.name}"
        assert EN_DASH not in blob, f"en dash in {p.name}"
        text = blob.decode("utf-8")
        for ch in text:
            cp = ord(ch)
            emoji = (0x1F000 <= cp <= 0x1FFFF or 0x2600 <= cp <= 0x27BF
                     or cp in (0x2B50, 0x2B55, 0xFE0F))
            assert not emoji, f"emoji U+{cp:04X} in {p.name}"


def test_no_banned_vocabulary_anywhere():
    word_re = re.compile(
        r"\b(" + "|".join(BANNED_WORDS) + r")\b", re.IGNORECASE)
    for p in _all_files():
        if p.suffix not in (".py", ".md", ".sql", ".txt", ".json", ".csv",
                            ".gitignore"):
            continue
        text = p.read_bytes().decode("utf-8")
        m = word_re.search(text)
        assert m is None, f"banned word {m.group(0)!r} in {p.name}"
        low = text.lower()
        for phrase in BANNED_PHRASES:
            assert phrase not in low, f"banned phrase in {p.name}"
        for sub in BANNED_SUBSTRINGS:
            assert sub not in low, f"banned substring in {p.name}"
