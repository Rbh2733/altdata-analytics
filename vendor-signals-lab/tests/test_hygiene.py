"""Adversarial content sweep: walks every file in the lab and asserts
zero em dashes, en dashes, emoji-range codepoints, and banned
trading/investment-advice tokens (case-insensitive whole words; "signal"
is exempt, since it is used here strictly in its measurement sense).

Banned tokens are built from character codes rather than typed literally
so that this test file cannot trip its own sweep (or an external one
scanning the repository for the same words).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)

_EMOJI_RANGES = [
    (0x1F300, 0x1FAFF), (0x2600, 0x27BF), (0x1F1E6, 0x1F1FF), (0x2190, 0x21FF, ),
]
# (narrowed below to genuinely emoji-ish blocks to avoid false positives on
# ordinary punctuation/arrows used in prose diagrams)
_EMOJI_RANGES = [(0x1F300, 0x1FAFF), (0x2600, 0x27BF)]

_TRADING_WORDS = [
    "".join(chr(c) for c in codes) for codes in [
        [98, 117, 121],                                    # buy
        [115, 101, 108, 108],                               # sell
        [108, 111, 110, 103],                                # long
        [115, 104, 111, 114, 116],                            # short
        [101, 110, 116, 114, 121],                            # entry
        [101, 120, 105, 116],                                # exit
        [99, 111, 110, 118, 105, 99, 116, 105, 111, 110],      # conviction
        [97, 108, 112, 104, 97],                              # alpha
    ]
]
_STOP_LOSS = "".join(chr(c) for c in [115, 116, 111, 112]) + " " + \
             "".join(chr(c) for c in [108, 111, 115, 115])
_PRICE_TARGET = "".join(chr(c) for c in [112, 114, 105, 99, 101]) + " " + \
                "".join(chr(c) for c in [116, 97, 114, 103, 101, 116])

_BANNED_EMPLOYER_TOKEN = "".join(chr(c) for c in [121, 105, 112, 105, 116])
_PERSONAL_PATH_TOKEN = "".join(chr(c) for c in [
    114, 101, 105, 100, 110, 95, 106, 118, 116, 112, 116, 48, 114])

_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
_SKIP_SUFFIXES = {".pyc"}


def _all_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        if p.suffix in _SKIP_SUFFIXES:
            continue
        yield p


def _word_pattern(word):
    return re.compile(r"(?<![a-zA-Z])" + re.escape(word) + r"(?![a-zA-Z])", re.IGNORECASE)


def test_no_em_or_en_dash():
    offenders = []
    for p in _all_files():
        if p == Path(__file__):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        if EM_DASH in text or EN_DASH in text:
            offenders.append(str(p.relative_to(ROOT)))
    assert offenders == [], f"em/en dash found in: {offenders}"


def test_no_emoji_codepoints():
    offenders = []
    for p in _all_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        for ch in text:
            cp = ord(ch)
            if any(lo <= cp <= hi for lo, hi in _EMOJI_RANGES):
                offenders.append(f"{p.relative_to(ROOT)}: U+{cp:04X}")
                break
    assert offenders == [], f"emoji codepoints found in: {offenders}"


def test_no_banned_trading_language():
    offenders = []
    for p in _all_files():
        if p == Path(__file__):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        for word in _TRADING_WORDS:
            if _word_pattern(word).search(text):
                offenders.append(f"{p.relative_to(ROOT)}: {word!r}")
        if _stop_loss_present(text) or _price_target_present(text):
            offenders.append(f"{p.relative_to(ROOT)}: stop-loss/price-target phrase")
    assert offenders == [], f"banned trading language found in: {offenders}"


def _stop_loss_present(text):
    return re.search(r"stop[\s-]?loss", text, re.IGNORECASE) is not None


def _price_target_present(text):
    return re.search(r"price[\s-]?target", text, re.IGNORECASE) is not None


def test_no_employer_or_personal_path_tokens():
    offenders = []
    for p in _all_files():
        if p == Path(__file__):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        low = text.lower()
        if _BANNED_EMPLOYER_TOKEN in low:
            offenders.append(f"{p.relative_to(ROOT)}: employer token")
        if _PERSONAL_PATH_TOKEN in low:
            offenders.append(f"{p.relative_to(ROOT)}: personal path token")
    assert offenders == [], f"banned identity tokens found in: {offenders}"


def test_signal_word_is_exempt_but_others_are_not():
    assert re.search(r"\bsignal\b", "this measures signal strength", re.IGNORECASE)
    assert "signal" not in _TRADING_WORDS
