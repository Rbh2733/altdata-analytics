"""Player-name normalization.

Copied from this repo's earlier baseball project, where every rule
corresponds to a real variation observed in the two actual datasets being
joined, not to a hypothetical one.

Observed variations, all real:
  accents          "Jasson Dominguez" in a ranking list vs "Jasson Dominguez"
                   with U+00ED in the MLB feed
  nickname vs legal  "Leo De Vries" (MLB's own useName) vs "Leodalis De Vries"
                   (his legal first name, and how he appears in some lists)
  initials         "JJ Wetherholt" vs "J.J. Wetherholt" vs legal "Jonathan"
  suffixes         "Jr.", "Sr.", "II", "III" attached inconsistently
  multi-word surnames  "De Vries", "Crow-Armstrong", "Smith-Shawver"
"""

import re
import unicodedata

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
_NON_NAME = re.compile(r"[^a-z ]")
_MULTISPACE = re.compile(r"\s{2,}")


def fold_accents(s: str) -> str:
    """NFKD decompose, then drop combining marks. Turns i-acute into i.

    Chosen over a hand-built character map because it covers every accent
    in the data (Spanish, and any other Latin diacritic) without enumerating
    them, and because both source datasets are genuine UTF-8.
    """
    decomposed = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def normalize(raw: str) -> str:
    """Lowercase, accent-folded, punctuation-stripped, suffix-stripped core.

    Hyphens become spaces rather than being deleted, so "Crow-Armstrong"
    and "Crow Armstrong" collapse to the same core. Periods are deleted
    rather than spaced, so "J.J." becomes "jj" and matches "JJ".
    """
    s = fold_accents(raw).lower().strip()
    s = s.replace(".", "")
    s = s.replace("-", " ")
    s = _NON_NAME.sub(" ", s)
    s = _MULTISPACE.sub(" ", s).strip()

    tokens = [t for t in s.split() if t not in SUFFIXES]
    return " ".join(tokens)


def initials_form(raw: str) -> str:
    """Collapse a leading multi-token first name to its initials.

    "J J Wetherholt" -> "jj wetherholt". Handles the case where a list
    writes out separated initials that the feed stores glued together.
    Returns the plain normalized form when there is nothing to collapse.
    """
    tokens = normalize(raw).split()
    if len(tokens) < 3:
        return normalize(raw)
    lead = tokens[:-1]
    if all(len(t) == 1 for t in lead):
        return "".join(lead) + " " + tokens[-1]
    return normalize(raw)


def name_keys(raw: str) -> set[str]:
    """Every normalized spelling this raw name could reasonably be indexed
    under. Used to build the lookup index on the player-universe side, where
    each player contributes several name fields."""
    keys = {normalize(raw), initials_form(raw)}
    return {k for k in keys if k}
