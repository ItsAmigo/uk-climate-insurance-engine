"""Domain types for hazard exposure.

Kept deliberately small in this Phase 1 slice: only the types needed for the
postcode-handling and coordinate-lookup layers. Subsidence and windstorm
enums land alongside their respective ingestion code once the data sources
are confirmed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

# Generous bounding box covering the UK including outlying islands (Shetland,
# Channel Islands). Used purely as a sanity check on coordinates loaded from
# external data — anything outside this is almost certainly a parse error.
UK_LAT_MIN, UK_LAT_MAX = 49.5, 61.0
UK_LON_MIN, UK_LON_MAX = -8.7, 2.1


class FloodZone(IntEnum):
    """Environment Agency flood-zone scheme used for England.

    The other UK nations publish their own zone schemes which we harmonise
    onto this one in the ingestion layer (decision to be logged in
    docs/methodology.md once the harmonisation is implemented).
    """

    ZONE_1 = 1  # low probability  (< 1 in 1 000 annual exceedance)
    ZONE_2 = 2  # medium  (1 in 1 000 to 1 in 100 fluvial / 1 in 200 tidal)
    ZONE_3 = 3  # high    (> 1 in 100 fluvial / 1 in 200 tidal; covers 3a + 3b)


class SubsidenceClass(IntEnum):
    """Coarse subsidence-risk classification driven by clay shrink-swell.

    Derived at lookup time from the BGS Soil Parent Material `SOIL_GROUP`
    field via the dominant-class rule (see `hazards.subsidence` and
    docs/methodology.md). Order is risk-monotonic: higher value = higher
    expected damage rate from clay-soil shrink and swell.
    """

    LOW = 1  # sand-dominated; minimal shrink-swell
    MEDIUM = 2  # mixed soils, peat, or chalk-influenced; moderate risk
    HIGH = 3  # clay-dominated; high shrink-swell risk


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


@dataclass(frozen=True, slots=True)
class Coordinate:
    """A WGS84 latitude / longitude pair, sanity-checked to be inside the UK bbox."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not (UK_LAT_MIN <= self.lat <= UK_LAT_MAX):
            raise ValueError(f"Latitude {self.lat} outside UK bounding box")
        if not (UK_LON_MIN <= self.lon <= UK_LON_MAX):
            raise ValueError(f"Longitude {self.lon} outside UK bounding box")


@dataclass(frozen=True, slots=True)
class HazardProfile:
    """The combined hazard exposure for a single coordinate / postcode.

    `windstorm_band` is None until the wind-data ingestion lands in a later
    Phase 1 slice; downstream consumers must treat None as "wind not yet
    modelled" rather than "no wind risk".
    """

    flood_zone: FloodZone
    subsidence_class: SubsidenceClass
    windstorm_band: int | None = None
