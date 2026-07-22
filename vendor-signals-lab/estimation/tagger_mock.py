"""Deterministic keyword-rule title classifier. No network, no key,
ships the published numbers. This is the default tagger `run_all.py`
uses; `tagger_claude.py` is a drop-in behind the same interface.

Rule order matters: phrase-level sales/support checks run first, then the
ml_infrastructure and research phrase checks, and only then the generic
"engineer" substring catch-all, so most titles resolve correctly. Three
deliberate exceptions survive by construction, all falling through to the
generic engineer rule against a different true label: "Support
Engineering Manager" (true support) matches none of the support phrases;
"ML Platform Engineer" (true ml_infrastructure) carries none of the
ml_infrastructure phrase anchors (no "infrastructure", no "gpu", no
"cluster"); and "Research Engineer" (true research) is neither a
"research scientist" nor a "researcher" by whole-word match. The
validation set measures all three confusions rather than hiding them.
"""

import re

FUNCTIONS = ["engineering", "ml_infrastructure", "research",
             "sales", "support", "other"]

_RULES = [
    (re.compile(r"\bsales\b"), "sales"),
    (re.compile(r"\baccount executive\b"), "sales"),
    (re.compile(r"\bbusiness development\b"), "sales"),
    (re.compile(r"\bchannel partner\b"), "sales"),
    (re.compile(r"\bregional sales\b"), "sales"),
    (re.compile(r"\bcustomer support\b"), "support"),
    (re.compile(r"\btechnical support\b"), "support"),
    (re.compile(r"\bsupport team\b"), "support"),
    (re.compile(r"\bcustomer success\b"), "support"),
    (re.compile(r"\bhelp desk\b"), "support"),
    (re.compile(r"\bimplementation specialist\b"), "support"),
    (re.compile(r"\b(ml|machine learning|ai) infrastructure\b"), "ml_infrastructure"),
    (re.compile(r"\bgpu\b"), "ml_infrastructure"),
    (re.compile(r"\bcluster\b"), "ml_infrastructure"),
    (re.compile(r"\bmlops\b"), "ml_infrastructure"),
    (re.compile(r"\bdistributed training\b"), "ml_infrastructure"),
    (re.compile(r"\binference\b"), "ml_infrastructure"),
    (re.compile(r"\bdatacenter\b"), "ml_infrastructure"),
    (re.compile(r"\bresearch scientist\b"), "research"),
    (re.compile(r"\bresearcher\b"), "research"),
    (re.compile(r"engineer"), "engineering"),
    (re.compile(r"\bdeveloper\b"), "engineering"),
    (re.compile(r"\bsoftware\b"), "engineering"),
    (re.compile(r"\bdata engineer\b"), "engineering"),
    (re.compile(r"\binfrastructure\b"), "engineering"),
]


def classify_title(title: str) -> str:
    t = title.lower()
    for pattern, func in _RULES:
        if pattern.search(t):
            return func
    return "other"


def tag_titles(titles) -> list:
    """Tags every row exactly once, in order, no drops."""
    return [classify_title(t) for t in titles]
