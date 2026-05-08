"""Domain types for hazard exposure.

Kept deliberately small in this Phase 1 slice: only the types needed for the
postcode-handling layer. Subsidence and windstorm enums land alongside their
respective ingestion code once the data sources are confirmed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class FloodZone(IntEnum):
    """Environment Agency flood-zone scheme used for England.

    The other UK nations publish their own zone schemes which we harmonise
    onto this one in the ingestion layer (decision to be logged in
    docs/methodology.md once the harmonisation is implemented).
    """

    ZONE_1 = 1  # low probability  (< 1 in 1 000 annual exceedance)
    ZONE_2 = 2  # medium  (1 in 1 000 to 1 in 100 fluvial / 1 in 200 tidal)
    ZONE_3 = 3  # high    (> 1 in 100 fluvial / 1 in 200 tidal; covers 3a + 3b)


@dataclass(frozen=True, slots=True)
class Postcode:
    """A validated, normalised UK postcode split into outward and inward parts."""

    outward: str
    inward: str

    @property
    def normalized(self) -> str:
        return f"{self.outward} {self.inward}"

    def __str__(self) -> str:
        return self.normalized
