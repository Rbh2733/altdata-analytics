"""Merchant-string normalization.

Turns a raw processor descriptor into the cleanest core string the matcher
can work with. Every rule here corresponds to a decoration the generator
seeds (and that real card feeds produce): processor prefixes, store numbers,
phone numbers, city tails, legal suffixes, doubled whitespace.

The junk pass runs twice on purpose. Store numbers and phone fragments are
often glued to the name behind punctuation ("BOX#4821"); they only become
strippable after punctuation is replaced with spaces, so a single pass
leaves them embedded in the core.
"""

import re

PROCESSOR_PREFIXES = re.compile(
    r"^(SQ \*|PAYPAL \*|PP\*|STRIPE\*|FS \*|IN \*|WEB\*)\s*"
)
TRAILING_JUNK = re.compile(
    r"(\s+#?\d{2,}|\s+STORE\s*\d+|\s+\d{3}-\d{3}-\d{4}|\s+\.COM|\s+INC\.?|\s+LLC"
    r"|\s+RENEWAL|\s+MONTHLY|\s+NYC|\s+AUSTIN TX)+$"
)
NON_ALNUM = re.compile(r"[^A-Z0-9&. ]")
MULTISPACE = re.compile(r"\s{2,}")


def normalize(raw: str) -> str:
    s = raw.upper().strip()
    s = PROCESSOR_PREFIXES.sub("", s)
    s = TRAILING_JUNK.sub("", s)
    s = NON_ALNUM.sub(" ", s)
    s = MULTISPACE.sub(" ", s).strip()
    s = TRAILING_JUNK.sub("", s)  # second pass: junk unmasked by punctuation removal
    return MULTISPACE.sub(" ", s).strip()
