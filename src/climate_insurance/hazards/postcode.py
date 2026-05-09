"""UK postcode normalisation, validation, and parsing.

Pure code — no data dependencies. Used by the postcode-to-hazard lookup
layer to canonicalise user input before any spatial join.

Format reference: a UK postcode is two parts separated by one space.
- Outward code: 1-2 letters + 1 digit + optionally 1 digit OR 1 letter
  (e.g. "SW1A", "M1", "B33", "EC1A", "W1A").
- Inward code: 1 digit + 2 letters (e.g. "1AA", "0AX").
- Special case: "GIR 0AA" (the historic Girobank postcode) does not
  follow the normal pattern but is valid.
"""

from __future__ import annotations

import re

from .types import Postcode

_POSTCODE_RE = re.compile(
    r"^(GIR 0AA|[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2})$",
)


def normalize_postcode(raw: str) -> str:
    """Return the canonical form: uppercase, exactly one space before the inward code.

    Whitespace anywhere in the input is collapsed; the inward code (final
    three characters) is split off with a single space inserted. Idempotent.

    >>> normalize_postcode(" sw1a1aa ")
    'SW1A 1AA'
    >>> normalize_postcode("m1  1ae")
    'M1 1AE'
    """
    stripped = re.sub(r"\s+", "", raw).upper()
    if len(stripped) < 5:
        return stripped  # too short to split — let validation reject it
    return f"{stripped[:-3]} {stripped[-3:]}"


def is_valid_postcode(raw: str) -> bool:
    """True if `raw` is a syntactically valid UK postcode (after normalising)."""
    return bool(_POSTCODE_RE.match(normalize_postcode(raw)))


def parse_postcode(raw: str) -> Postcode:
    """Normalise and validate `raw`; return a `Postcode` or raise ValueError."""
    normalized = normalize_postcode(raw)
    if not _POSTCODE_RE.match(normalized):
        raise ValueError(f"Not a valid UK postcode: {raw!r}")
    outward, inward = normalized.split(" ", 1)
    return Postcode(outward=outward, inward=inward)
