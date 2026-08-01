"""Throttled, cached MLB Stats API client.

Design carried over from the verified client in this repo's earlier baseball
project (hand-checked endpoints, request timeouts, fail-loud validation),
with two additions that project lacked and this one needs for a
thousand-call historical pull: a polite throttle between real network hits
and a local response cache so reruns cost zero calls. MLBAM's terms permit
individual, non-commercial, non-bulk use; the cache and throttle exist to
keep this project comfortably inside that.

All responses are cached to data/cache keyed on the full URL. Delete the
cache directory to force a refetch.
"""

import hashlib
import json
import time
import urllib.parse
import urllib.request

import config

THROTTLE_SECONDS = 0.45
TIMEOUT = 45
RETRIES = 3

_last_hit = [0.0]


def _cache_path(url: str):
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return config.DATA_CACHE / f"{digest}.json"


def get_json(path: str, params: dict | None = None) -> dict:
    """GET an API path, throttled and cached. path starts with /v1."""
    url = config.MLB_STATS_API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    cpath = _cache_path(url)
    if cpath.exists():
        return json.loads(cpath.read_text(encoding="utf-8"))

    config.DATA_CACHE.mkdir(parents=True, exist_ok=True)
    last_err = None
    for attempt in range(RETRIES):
        wait = THROTTLE_SECONDS - (time.monotonic() - _last_hit[0])
        if wait > 0:
            time.sleep(wait)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mlb-pipeline-analyzer/1.0 (personal research)"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
            _last_hit[0] = time.monotonic()
            data = json.loads(body)
            cpath.write_text(body, encoding="utf-8")
            return data
        except Exception as err:  # noqa: BLE001 - retried, then raised
            _last_hit[0] = time.monotonic()
            last_err = err
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"API call failed after {RETRIES} attempts: {url}") from last_err


def year_by_year(player_id: int, group: str, sport_id: int) -> list[dict]:
    """All seasons for one player at one sport level, one call.

    Verified live 2026-08-01: yearByYear returns MLB only unless sportId is
    passed, and the plural sportIds parameter is silently ignored, so the
    fetch is one call per (player, group, sport).
    """
    data = get_json(f"/v1/people/{player_id}/stats",
                    {"stats": "yearByYear", "group": group, "sportId": sport_id})
    stats = data.get("stats", [])
    return stats[0].get("splits", []) if stats else []


def game_log(player_id: int, season: int, group: str, sport_id: int) -> list[dict]:
    """Dated per-game rows for one player, season, level.

    gameLog is the only fenceable stat surface (byDateRange returns empty on
    this API, verified live), which is what makes the debut-season cutoff
    possible.
    """
    data = get_json(f"/v1/people/{player_id}/stats",
                    {"stats": "gameLog", "season": season, "group": group,
                     "sportId": sport_id})
    stats = data.get("stats", [])
    return stats[0].get("splits", []) if stats else []


def teams_stats(sport_id: int, season: int, group: str) -> list[dict]:
    """Per-team season stat lines for a whole level-season, one call."""
    data = get_json("/v1/teams/stats",
                    {"sportId": sport_id, "season": season, "group": group,
                     "stats": "season"})
    stats = data.get("stats", [])
    return stats[0].get("splits", []) if stats else []


def sports_players(sport_id: int, season: int) -> list[dict]:
    """Every player who appeared at a level in a season, one bulk call."""
    data = get_json(f"/v1/sports/{sport_id}/players", {"season": season})
    return data.get("people", [])
