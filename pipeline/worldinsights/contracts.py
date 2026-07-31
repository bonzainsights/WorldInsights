"""Canonical contracts shared by ingestion, compatibility, and serving layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import StrEnum
from math import isfinite


class GeographyType(StrEnum):
    COUNTRY = "country"
    TERRITORY = "territory"
    REGION = "region"
    AGGREGATE = "aggregate"


class Frequency(StrEnum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    IRREGULAR = "irregular"


class ObservationStatus(StrEnum):
    OBSERVED = "observed"
    ESTIMATED = "estimated"
    MODELED = "modeled"
    PROVISIONAL = "provisional"
    REVISED = "revised"
    SUPPRESSED = "suppressed"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


class MeasurementType(StrEnum):
    STOCK = "stock"
    FLOW = "flow"
    RATE = "rate"
    RATIO = "ratio"
    INDEX = "index"
    CURRENCY = "currency"


@dataclass(frozen=True, slots=True)
class Geography:
    geography_id: int
    canonical_code: str
    name: str
    geography_type: GeographyType
    parent_id: int | None = None
    valid_from: date | None = None
    valid_to: date | None = None

    def __post_init__(self) -> None:
        if self.geography_id <= 0:
            raise ValueError("geography_id must be positive")
        if not self.canonical_code.strip():
            raise ValueError("canonical_code is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if self.parent_id == self.geography_id:
            raise ValueError("a geography cannot be its own parent")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("valid_from cannot be after valid_to")


@dataclass(frozen=True, slots=True)
class Period:
    start: date
    end: date
    frequency: Frequency
    label: str

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("period start cannot be after period end")
        if not self.label.strip():
            raise ValueError("period label is required")

    @classmethod
    def annual(cls, year: int) -> Period:
        if year < 1:
            raise ValueError("year must be positive")
        return cls(
            start=date(year, 1, 1),
            end=date(year, 12, 31),
            frequency=Frequency.ANNUAL,
            label=str(year),
        )


@dataclass(frozen=True, slots=True)
class Unit:
    unit_id: str
    name: str
    symbol: str
    dimension: str
    scale: float = 1.0
    currency: str | None = None
    price_basis: str | None = None
    base_year: int | None = None
    denominator: str | None = None

    def __post_init__(self) -> None:
        if not self.unit_id.strip() or not self.name.strip() or not self.dimension.strip():
            raise ValueError("unit_id, name, and dimension are required")
        if not isfinite(self.scale) or self.scale <= 0:
            raise ValueError("unit scale must be finite and positive")
        if self.base_year is not None and self.base_year < 1:
            raise ValueError("base_year must be positive")


@dataclass(frozen=True, slots=True)
class CanonicalConcept:
    concept_id: str
    name: str
    description: str
    dimension: str
    measurement_type: MeasurementType
    aggregation_behavior: str

    def __post_init__(self) -> None:
        required = (
            self.concept_id,
            self.name,
            self.description,
            self.dimension,
            self.aggregation_behavior,
        )
        if any(not value.strip() for value in required):
            raise ValueError("canonical concept fields cannot be empty")


@dataclass(frozen=True, slots=True)
class IndicatorVariant:
    indicator_variant_id: str
    provider_id: str
    dataset_id: str
    provider_indicator_code: str
    name: str
    concept_id: str
    unit_id: str
    frequency: Frequency
    geography_types: frozenset[GeographyType]

    def __post_init__(self) -> None:
        required = (
            self.indicator_variant_id,
            self.provider_id,
            self.dataset_id,
            self.provider_indicator_code,
            self.name,
            self.concept_id,
            self.unit_id,
        )
        if any(not value.strip() for value in required):
            raise ValueError("indicator variant fields cannot be empty")
        if not self.geography_types:
            raise ValueError("indicator must support at least one geography type")


@dataclass(frozen=True, slots=True)
class DataRelease:
    release_id: str
    provider_id: str
    dataset_id: str
    retrieved_at: datetime
    source_checksum: str
    pipeline_version: str

    def __post_init__(self) -> None:
        required = (
            self.release_id,
            self.provider_id,
            self.dataset_id,
            self.source_checksum,
            self.pipeline_version,
        )
        if any(not value.strip() for value in required):
            raise ValueError("release fields cannot be empty")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")

    @classmethod
    def create(
        cls,
        *,
        release_id: str,
        provider_id: str,
        dataset_id: str,
        source_checksum: str,
        pipeline_version: str,
    ) -> DataRelease:
        return cls(
            release_id=release_id,
            provider_id=provider_id,
            dataset_id=dataset_id,
            retrieved_at=datetime.now(timezone.utc),
            source_checksum=source_checksum,
            pipeline_version=pipeline_version,
        )


@dataclass(frozen=True, slots=True)
class Observation:
    release_id: str
    indicator_variant_id: str
    geography_id: int
    period: Period
    unit_id: str
    status: ObservationStatus
    value: float | None
    provider_quality_flags: tuple[str, ...] = field(default_factory=tuple)
    system_quality_flags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.release_id.strip() or not self.indicator_variant_id.strip():
            raise ValueError("release and indicator IDs are required")
        if self.geography_id <= 0:
            raise ValueError("geography_id must be positive")
        if not self.unit_id.strip():
            raise ValueError("unit_id is required")

        value_required = self.status in {
            ObservationStatus.OBSERVED,
            ObservationStatus.ESTIMATED,
            ObservationStatus.MODELED,
            ObservationStatus.PROVISIONAL,
            ObservationStatus.REVISED,
        }
        if value_required and self.value is None:
            raise ValueError(f"{self.status} observations require a value")
        if not value_required and self.value is not None:
            raise ValueError(f"{self.status} observations must not contain a value")
        if self.value is not None and not isfinite(self.value):
            raise ValueError("observation value must be finite")
