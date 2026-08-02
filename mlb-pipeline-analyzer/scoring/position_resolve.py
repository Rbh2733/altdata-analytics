"""Decides which position(s) feed a player's positional adjustment, per
Reid's ruling 2026-08-01.

The rule, in its final form:
  single position listed          use it as-is. "INF" is a special case
                                   of this, see constants.py, it is graded
                                   at shortstop's value directly rather
                                   than a blended average, Reid's reasoning
                                   being that an unspecified "he can play
                                   the infield" label is itself the
                                   high-value signal, not a hedge.
  multiple positions listed,
    one of the 7 Reid reviewed    use his specific call outright
  multiple positions listed,
    everyone else                 average the position-adjustment
                                   constant across every position listed,
                                   infield-only combos included, no
                                   special-casing

An earlier version of this rule tried resolving multi-position combos by
picking a single "winner" via real games-played data, then by taking the
highest value among pure-infield combos specifically. Both were corrected
by Reid the same day, "you misunderstood." Real games-played data
(data/derived/current_position.csv) still feeds the position_today
DISPLAY column, unrelated to this scoring logic.
"""


def resolve_position(ranking_position: str, manual_override: str | None = None) -> dict:
    """Returns {"positions": [str, ...], "basis": str}.

    positions is always a list, even for the single-position case, so the
    caller can average uniformly (average of one value is just that
    value).

    manual_override, when given, is itself split the same way as
    ranking_position, so a review can pin a single position ("CF") or
    still average across a corrected set (Miguel Vargas, 3B/OF/1B on the
    list, corrected to 3B/1B, dropping OF from consideration entirely
    rather than picking one of the remaining two).

    basis is one of:
      single           only one position was ever listed. "INF" is
                        included here, its shortstop-level grading lives
                        in the constants table, not a resolution branch.
      reid_confirmed    a case reviewed and settled by hand
                        (data/raw/position_overrides.csv)
      averaged         multiple positions listed, no human review, the
                        position-adjustment constant is averaged across
                        every one the list named
    """
    tokens = [t.strip().upper() for t in (ranking_position or "").split("/") if t.strip()]

    if manual_override:
        override_tokens = [t.strip().upper() for t in manual_override.split("/") if t.strip()]
        return {"positions": override_tokens, "basis": "reid_confirmed"}

    if len(tokens) <= 1:
        return {"positions": tokens, "basis": "single"}

    return {"positions": tokens, "basis": "averaged"}
