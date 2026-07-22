"""Deterministic keyword-rule title classifier. No network, no key,
ships the published numbers. This is the default tagger `run_all.py`
uses; `tagger_claude.py` is a drop-in behind the same interface.

Rule order matters: phrase-level sales/support checks run before the
generic "engineer" substring catch-all, so most titles resolve
correctly. One deliberate exception survives by construction: "Support
Engineering Manager" does not match any of the support phrases (it is
not "customer support", "technical support", or "support team") so it
falls through to the generic engineer rule and is mistagged engineering
against a true label of support. That single template is the tagger's
one designed confusion; the validation set measures it rather than
hiding it.
"""

import re

FUNCTIONS = ["engineering", "sales", "support", "other"]

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
