"""Name normalization rules, each tied to a real variation in the data."""

import pytest

from matching.normalize_name import normalize, initials_form, fold_accents, name_keys


@pytest.mark.parametrize("raw,expected", [
    ("Jesús Made", "jesus made"),
    ("Jasson Domínguez", "jasson dominguez"),
    ("Ronald Acuña Jr.", "ronald acuna"),
    ("Luisangel Acuña", "luisangel acuna"),
])
def test_accents_folded(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("Ronald Acuna Jr.", "ronald acuna"),
    ("Ronald Acuna Jr", "ronald acuna"),
    ("Bobby Witt Jr.", "bobby witt"),
    ("Vladimir Guerrero III", "vladimir guerrero"),
])
def test_suffixes_stripped(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("Pete Crow-Armstrong", "pete crow armstrong"),
    ("Pete Crow Armstrong", "pete crow armstrong"),
    ("AJ Smith-Shawver", "aj smith shawver"),
])
def test_hyphens_become_spaces(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("J.J. Wetherholt", "jj wetherholt"),
    ("JJ Wetherholt", "jj wetherholt"),
])
def test_periods_deleted_not_spaced(raw, expected):
    """Deleting rather than spacing is what makes 'J.J.' equal 'JJ'."""
    assert normalize(raw) == expected


def test_separated_initials_collapse():
    assert initials_form("J J Wetherholt") == "jj wetherholt"


def test_initials_form_leaves_real_names_alone():
    """A genuine three-token name must not be mangled into initials."""
    assert initials_form("Jonathan David Wetherholt") == "jonathan david wetherholt"


def test_multiword_surname_preserved():
    assert normalize("Leo De Vries") == "leo de vries"


def test_fold_accents_is_pure_transliteration():
    assert fold_accents("Acuña") == "Acuna"
    assert fold_accents("Rodríguez") == "Rodriguez"


def test_name_keys_includes_both_forms():
    keys = name_keys("J J Wetherholt")
    assert "jj wetherholt" in keys
