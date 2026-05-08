"""Tests for postcode normalisation, validation, and parsing."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from climate_insurance.hazards import (
    Postcode,
    is_valid_postcode,
    normalize_postcode,
    parse_postcode,
)

# Real postcodes covering each Royal Mail format variant + the GIR special case.
VALID_CASES: list[tuple[str, str, str, str]] = [
    # raw, expected normalized, expected outward, expected inward
    ("SW1A 1AA", "SW1A 1AA", "SW1A", "1AA"),  # AA9A 9AA — central London
    ("M1 1AE", "M1 1AE", "M1", "1AE"),  # A9 9AA — Manchester
    ("B33 8TH", "B33 8TH", "B33", "8TH"),  # A99 9AA — Birmingham
    ("CR2 6XH", "CR2 6XH", "CR2", "6XH"),  # AA9 9AA — Croydon
    ("DN55 1PT", "DN55 1PT", "DN55", "1PT"),  # AA99 9AA — Doncaster
    ("EC1A 1BB", "EC1A 1BB", "EC1A", "1BB"),  # AA9A 9AA
    ("W1A 0AX", "W1A 0AX", "W1A", "0AX"),  # A9A 9AA — BBC HQ
    ("GIR 0AA", "GIR 0AA", "GIR", "0AA"),  # historic Girobank
    # Whitespace + case variants must normalise to the canonical form.
    ("sw1a1aa", "SW1A 1AA", "SW1A", "1AA"),
    (" sw1a 1aa ", "SW1A 1AA", "SW1A", "1AA"),
    ("M1  1AE", "M1 1AE", "M1", "1AE"),
    ("\tEC1A\n1BB", "EC1A 1BB", "EC1A", "1BB"),
]


@pytest.mark.parametrize("raw,expected_normalized,_outward,_inward", VALID_CASES)
def test_normalize_postcode_canonicalizes_input(
    raw: str, expected_normalized: str, _outward: str, _inward: str
) -> None:
    assert normalize_postcode(raw) == expected_normalized


@pytest.mark.parametrize("raw,_normalized,_outward,_inward", VALID_CASES)
def test_is_valid_postcode_accepts_all_formats(
    raw: str, _normalized: str, _outward: str, _inward: str
) -> None:
    assert is_valid_postcode(raw) is True


@pytest.mark.parametrize("raw,expected_normalized,outward,inward", VALID_CASES)
def test_parse_postcode_splits_outward_and_inward(
    raw: str, expected_normalized: str, outward: str, inward: str
) -> None:
    parsed = parse_postcode(raw)
    assert parsed == Postcode(outward=outward, inward=inward)
    assert parsed.normalized == expected_normalized
    assert str(parsed) == expected_normalized


@pytest.mark.parametrize(
    "raw",
    [
        "",
        " ",
        "NOT-A-POSTCODE",
        "12345",
        "SW1A",  # outward only
        "1AA",  # inward only
        "SW1A 1A",  # inward too short
        "SW1A 1AAA",  # inward too long
        "SSSS 1AA",  # too many leading letters
        "SW1A 1A1",  # digit in inward letters
        "ZZZZ ZZZ",  # pure letters
    ],
)
def test_invalid_inputs_are_rejected(raw: str) -> None:
    assert is_valid_postcode(raw) is False
    with pytest.raises(ValueError):
        parse_postcode(raw)


@given(st.sampled_from([case[0] for case in VALID_CASES]))
def test_normalize_is_idempotent_on_valid_inputs(raw: str) -> None:
    once = normalize_postcode(raw)
    twice = normalize_postcode(once)
    assert once == twice


@given(st.text(max_size=20))
def test_normalize_never_raises(raw: str) -> None:
    """Normalisation is total — only validation/parsing may reject input."""
    normalize_postcode(raw)
