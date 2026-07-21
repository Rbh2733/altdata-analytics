"""Deterministic generator for the synthetic streaming-catalog seed.

Produces streaming_analytics/seeds/streaming_tracks_raw.csv: 85,000 track
rows for a fictional music-streaming catalog. Every artist, album, track,
and record label name is invented; no real catalog data is used or implied.

The output is byte-stable: fixed RNG seed, single Random instance with a
fixed draw order, fixed numeric formatting, and Unix line endings. Running
this script twice produces byte-identical files, so the committed seed can
be verified by regenerating and diffing.

Usage (from the repository's dbt-streaming-analytics directory):

    python scripts/generate_seed.py

The row count and value ranges are chosen to satisfy every dbt test in the
project (see streaming_analytics/tests/ and the schema yml files).
"""

import csv
import hashlib
import random
from pathlib import Path

SEED = 11
N_TRACKS = 85_000
OUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "streaming_analytics"
    / "seeds"
    / "streaming_tracks_raw.csv"
)

HEADER = [
    "track_id", "track_name", "artist_name", "album_name", "release_date",
    "genre", "duration_ms", "popularity", "danceability", "energy", "key",
    "loudness", "mode", "instrumentalness", "tempo", "stream_count",
    "country", "explicit", "label",
]

# Genre sound profiles: (danceability, energy, tempo, loudness,
# instrumentalness, explicit_rate, duration_ms mean, sampling weight).
# The feature means are loosely modeled on how these genres tend to
# score on published audio-feature scales, then noised per artist and
# per track. All values stay inside the ranges the dbt tests assert.
GENRES = {
    "Pop":       (0.68, 0.65, 118, -7.0, 0.05, 0.15, 205_000, 18),
    "Rock":      (0.50, 0.72, 128, -8.0, 0.10, 0.18, 232_000, 12),
    "Hip-Hop":   (0.78, 0.68,  95, -6.5, 0.03, 0.55, 198_000, 15),
    "Metal":     (0.42, 0.88, 142, -5.5, 0.18, 0.30, 262_000,  6),
    "Indie":     (0.55, 0.55, 115, -10.0, 0.15, 0.12, 218_000,  9),
    "Country":   (0.58, 0.58, 112, -8.5, 0.04, 0.05, 202_000,  8),
    "Classical": (0.25, 0.25,  90, -20.0, 0.82, 0.00, 320_000,  5),
    "EDM":       (0.72, 0.85, 128, -5.0, 0.45, 0.08, 240_000,  9),
    "Jazz":      (0.45, 0.40, 105, -13.0, 0.55, 0.02, 285_000,  5),
    "R&B":       (0.70, 0.55, 100, -8.0, 0.05, 0.30, 212_000,  7),
    "Folk":      (0.48, 0.38, 100, -12.0, 0.20, 0.04, 215_000,  4),
    "Reggaeton": (0.80, 0.75,  96, -6.0, 0.03, 0.35, 200_000,  6),
}
GENRE_NAMES = list(GENRES)
GENRE_WEIGHTS = [GENRES[g][7] for g in GENRE_NAMES]

# Fictional record labels with market-share weights (three majors, three
# mid-tier, two boutique). Names are invented for this dataset.
LABELS = [
    ("Meridian Records", 22),
    ("Halcyon Music Group", 18),
    ("Bluewater Sound", 15),
    ("Northline Music", 11),
    ("Foxglove Records", 9),
    ("Cassette Club Records", 9),
    ("Aurora Peak Audio", 9),
    ("Paper Lantern Music", 7),
]
LABEL_NAMES = [l[0] for l in LABELS]
LABEL_WEIGHTS = [l[1] for l in LABELS]

COUNTRIES = [
    ("United States", 24), ("United Kingdom", 12), ("Germany", 9),
    ("France", 8), ("Brazil", 9), ("Japan", 8), ("Canada", 7),
    ("Australia", 6), ("Mexico", 7), ("South Korea", 5),
    ("Sweden", 3), ("Spain", 4),
]
COUNTRY_NAMES = [c[0] for c in COUNTRIES]
COUNTRY_WEIGHTS = [c[1] for c in COUNTRIES]

FIRST_NAMES = [
    "Ada", "Aiden", "Alma", "Amara", "Andre", "Anika", "Ari", "Asha",
    "August", "Aurelia", "Beck", "Bianca", "Bram", "Briar", "Callum",
    "Camille", "Caspian", "Cato", "Celia", "Cormac", "Dahlia", "Dante",
    "Delia", "Dorian", "Eamon", "Edith", "Eloise", "Emrys", "Enzo",
    "Esme", "Ezra", "Farah", "Felix", "Fern", "Finnian", "Freya",
    "Gideon", "Greta", "Hale", "Harriet", "Hollis", "Ida", "Ines",
    "Ira", "Isolde", "Jasper", "Jonas", "Juniper", "Kai", "Keira",
    "Lachlan", "Leda", "Lennon", "Lior", "Lucia", "Magnus", "Maren",
    "Matteo", "Mavis", "Milo", "Mira", "Nadia", "Nell", "Nico",
    "Noor", "Odessa", "Orin", "Otto", "Paloma", "Pax", "Petra",
    "Quill", "Rafferty", "Ramona", "Reuben", "Rhea", "Roscoe", "Rosalind",
    "Sable", "Saffron", "Sasha", "Selene", "Silas", "Sonia", "Soren",
    "Tamsin", "Teodoro", "Thea", "Tobias", "Una", "Vada", "Vera",
    "Wallace", "Wren", "Xavier", "Yara", "Yusuf", "Zadie", "Zane", "Zora",
]
LAST_NAMES = [
    "Abernathy", "Alcott", "Amsel", "Arbor", "Ashdown", "Atwater",
    "Ballinger", "Barlowe", "Beaufort", "Bellweather", "Birchall",
    "Blackwood", "Bramwell", "Briggs", "Calloway", "Carrow", "Cashel",
    "Chamberlin", "Colefax", "Corliss", "Crane", "Cresswell", "Dashwood",
    "Delacroix", "Dunmore", "Eastgate", "Ellery", "Elmswood", "Fairbanks",
    "Fenwick", "Fielding", "Fontaine", "Forsythe", "Gable", "Gallow",
    "Gathright", "Glenholme", "Greaves", "Hargrove", "Hartwell",
    "Hawthorne", "Heathcote", "Holloway", "Huxley", "Ingram", "Ivers",
    "Kearney", "Kingsley", "Lachance", "Lambert", "Larkspur", "Ledger",
    "Linfield", "Lockridge", "Lovelace", "Mabry", "Marchetti", "Merrick",
    "Montrose", "Mortlake", "Nettleton", "Nightingale", "Northway",
    "Oakhurst", "Oberlin", "Ormond", "Palgrave", "Pemberton", "Penrose",
    "Quimby", "Radcliffe", "Ravenscroft", "Redfern", "Renshaw", "Rockwell",
    "Rosewood", "Rutherford", "Sandoval", "Selwyn", "Shackleton",
    "Silvestri", "Sinclair", "Southwell", "Stanhope", "Stillwater",
    "Summerfield", "Tallis", "Thackeray", "Thistlewood", "Trelawney",
    "Underhill", "Vance", "Vesper", "Wakefield", "Waverly", "Westbrook",
    "Whitfield", "Winslow", "Wolfe", "Yardley",
]
ADJECTIVES = [
    "Amber", "Ashen", "Broken", "Burning", "Copper", "Crimson", "Distant",
    "Electric", "Endless", "Fading", "Feral", "Frozen", "Gilded", "Golden",
    "Hidden", "Hollow", "Howling", "Iron", "Lonely", "Lucid", "Midnight",
    "Neon", "Northern", "Paper", "Quiet", "Restless", "Rising", "Rusted",
    "Sapphire", "Scarlet", "Silent", "Silver", "Sleepless", "Sunken",
    "Tidal", "Velvet", "Violet", "Wandering", "Wild", "Winter",
]
NOUNS = [
    "Anchor", "Arrow", "Avenue", "Beacon", "Bell", "Border", "Canyon",
    "Cinder", "Circuit", "Comet", "Compass", "Crown", "Current", "Dawn",
    "Ember", "Engine", "Fable", "Fathom", "Flare", "Fox", "Garden",
    "Ghost", "Glacier", "Harbor", "Horizon", "Hour", "Lantern", "Meadow",
    "Mirror", "Monarch", "Motive", "Oracle", "Orchard", "Parade", "Pilot",
    "Prairie", "Relay", "River", "Rocket", "Satellite", "Shadow", "Signal",
    "Sparrow", "Spire", "Static", "Summit", "Thicket", "Tide", "Vault",
    "Voyage",
]
VERBS = [
    "Chase", "Follow", "Forget", "Hold", "Leave", "Outrun", "Remember",
    "Steal", "Wake", "Watch",
]


def build_artist_names(rng, count):
    """Return `count` unique artist names, deterministically ordered."""
    persons = [f"{f} {l}" for f in FIRST_NAMES for l in LAST_NAMES]
    initials = "ABCDEFGHJKLMNPRSTVW"
    persons += [
        f"{f} {initials[(i + j) % len(initials)]}. {l}"
        for i, f in enumerate(FIRST_NAMES)
        for j, l in enumerate(LAST_NAMES)
    ]
    bands = []
    for adj in ADJECTIVES:
        for noun in NOUNS:
            bands.append(f"The {adj} {noun}s")
            bands.append(f"{adj} {noun}")
    for a in NOUNS:
        for b in NOUNS:
            if a != b:
                bands.append(f"{a} {b}")
    for noun in NOUNS:
        for last in LAST_NAMES[:40]:
            bands.append(f"{last} {noun} Club")
    for f in FIRST_NAMES:
        for noun in NOUNS[:40]:
            bands.append(f"{f} & the {noun}s")
    candidates = list(dict.fromkeys(persons + bands))
    rng.shuffle(candidates)
    if count > len(candidates):
        raise ValueError("not enough unique artist name candidates")
    return candidates[:count]


def make_title(rng):
    pattern = rng.randrange(6)
    if pattern == 0:
        return f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)}"
    if pattern == 1:
        return rng.choice(NOUNS)
    if pattern == 2:
        return f"{rng.choice(VERBS)} the {rng.choice(NOUNS)}"
    if pattern == 3:
        return f"{rng.choice(NOUNS)} in the {rng.choice(NOUNS)}"
    if pattern == 4:
        return f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)}s"
    return f"No More {rng.choice(NOUNS)}s"


def clamp(value, low, high):
    return max(low, min(high, value))


def draw_track_count(rng):
    """Tracks per artist: mostly singles, with a heavy tail of deep catalogs."""
    roll = rng.random()
    if roll < 0.55:
        return 1
    if roll < 0.73:
        return 2
    if roll < 0.82:
        return 3
    if roll < 0.94:
        return rng.randint(4, 8)
    if roll < 0.99:
        return rng.randint(9, 20)
    return rng.randint(21, 60)


def main():
    rng = random.Random(SEED)
    # Draw more artist names than we will need; generation stops at N_TRACKS.
    artist_names = build_artist_names(rng, 32_000)

    rows = []
    used_ids = set()
    total = 0
    for artist_name in artist_names:
        if total >= N_TRACKS:
            break
        n_tracks = min(draw_track_count(rng), N_TRACKS - total)
        genre = rng.choices(GENRE_NAMES, weights=GENRE_WEIGHTS, k=1)[0]
        label = rng.choices(LABEL_NAMES, weights=LABEL_WEIGHTS, k=1)[0]
        country = rng.choices(COUNTRY_NAMES, weights=COUNTRY_WEIGHTS, k=1)[0]
        start_year = rng.randint(2015, 2025)
        end_year = min(2025, start_year + rng.randint(0, 10))
        base_popularity = clamp(rng.gauss(45, 15), 5, 90)
        offsets = {
            "danceability": rng.gauss(0, 0.06),
            "energy": rng.gauss(0, 0.06),
            "tempo": rng.gauss(0, 6),
        }

        # Split the artist's tracks into albums of 1 to 8 tracks.
        album_sizes = []
        remaining = n_tracks
        while remaining > 0:
            size = min(rng.randint(1, 8), remaining)
            album_sizes.append(size)
            remaining -= size

        track_index = 0
        for album_size in album_sizes:
            album_name = make_title(rng)
            for _ in range(album_size):
                track_index += 1
                total += 1

                # Occasionally a track lands outside the artist's usual
                # genre, label, or home market.
                t_genre = genre
                if rng.random() < 0.12:
                    t_genre = rng.choices(
                        GENRE_NAMES, weights=GENRE_WEIGHTS, k=1)[0]
                t_label = label
                if rng.random() < 0.05:
                    t_label = rng.choices(
                        LABEL_NAMES, weights=LABEL_WEIGHTS, k=1)[0]
                t_country = country
                if rng.random() < 0.20:
                    t_country = rng.choices(
                        COUNTRY_NAMES, weights=COUNTRY_WEIGHTS, k=1)[0]

                (g_dance, g_energy, g_tempo, g_loud, g_instr, g_explicit,
                 g_duration, _w) = GENRES[t_genre]

                year = rng.randint(start_year, end_year)
                month = rng.randint(1, 12)
                day = rng.randint(1, 28)
                release_date = f"{year:04d}-{month:02d}-{day:02d}"

                popularity = int(round(clamp(
                    base_popularity + rng.gauss(0, 8), 0, 100)))
                streams = int(round(
                    2.718281828 ** rng.gauss(6.0 + 0.06 * popularity, 1.2)))
                streams = max(streams, 50)

                duration_ms = int(round(clamp(
                    rng.gauss(g_duration, 35_000), 45_000, 1_200_000)))
                danceability = clamp(
                    g_dance + offsets["danceability"] + rng.gauss(0, 0.08),
                    0.01, 0.99)
                energy = clamp(
                    g_energy + offsets["energy"] + rng.gauss(0, 0.08),
                    0.01, 0.99)
                tempo = clamp(
                    rng.gauss(g_tempo + offsets["tempo"], 18), 55, 220)
                loudness = clamp(rng.gauss(g_loud, 4), -55, -1)
                instrumentalness = clamp(
                    g_instr + rng.gauss(0, 0.15), 0.0, 0.98)
                musical_key = rng.randint(0, 11)
                musical_mode = 1 if rng.random() < 0.6 else 0
                explicit = 1 if rng.random() < g_explicit else 0

                raw_id = hashlib.md5(
                    f"seed-{SEED}-track-{total}".encode()).hexdigest()
                track_id = f"TRK-{raw_id[:12].upper()}"
                bump = 0
                while track_id in used_ids:
                    bump += 1
                    raw_id = hashlib.md5(
                        f"seed-{SEED}-track-{total}-{bump}".encode()
                    ).hexdigest()
                    track_id = f"TRK-{raw_id[:12].upper()}"
                used_ids.add(track_id)

                rows.append([
                    track_id,
                    make_title(rng),
                    artist_name,
                    album_name,
                    release_date,
                    t_genre,
                    str(duration_ms),
                    str(popularity),
                    f"{danceability:.3f}",
                    f"{energy:.3f}",
                    str(musical_key),
                    f"{loudness:.2f}",
                    str(musical_mode),
                    f"{instrumentalness:.3f}",
                    f"{tempo:.2f}",
                    str(streams),
                    t_country,
                    str(explicit),
                    t_label,
                ])

    rng.shuffle(rows)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
