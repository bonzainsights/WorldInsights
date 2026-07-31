"""Fast compatibility evaluation from compact indicator metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from functools import reduce
from operator import and_

from worldinsights.contracts import Frequency, GeographyType


class Operation(StrEnum):
    MAP = "map"
    TREND = "trend"
    TABLE = "table"
    SCATTER = "scatter"
    RATIO = "ratio"
    CORRELATION = "correlation"


class CompatibilityStatus(StrEnum):
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"


class CompatibilityClass(StrEnum):
    EXACT = "exact"
    CONVERTIBLE = "convertible"
    ALIGNABLE = "alignable"
    CONTEXTUAL = "contextual"
    INCOMPATIBLE = "incompatible"


class ReasonCode(StrEnum):
    NO_INDICATORS = "no_indicators"
    OPERATION_ARITY = "operation_arity"
    NO_SHARED_GEOGRAPHIES = "no_shared_geographies"
    NO_SHARED_PERIODS = "no_shared_periods"
    NO_SHARED_GEOGRAPHY_TYPE = "no_shared_geography_type"
    FREQUENCY_MISMATCH = "frequency_mismatch"
    CONCEPT_MISMATCH = "concept_mismatch"
    UNIT_MISMATCH = "unit_mismatch"
    CONTEXTUAL_COMPARISON = "contextual_comparison"


@dataclass(frozen=True, slots=True)
class CoverageIndex:
    indicator_variant_id: str
    geography_bits: int
    periods: frozenset[str]
    geography_types: frozenset[GeographyType]
    frequency: Frequency
    concept_id: str
    unit_id: str

    def __post_init__(self) -> None:
        if not self.indicator_variant_id.strip():
            raise ValueError("indicator_variant_id is required")
        if self.geography_bits < 0:
            raise ValueError("geography_bits cannot be negative")
        if not self.geography_types:
            raise ValueError("at least one geography type is required")
        if not self.concept_id.strip() or not self.unit_id.strip():
            raise ValueError("concept_id and unit_id are required")

    @classmethod
    def from_geography_ids(
        cls,
        *,
        indicator_variant_id: str,
        geography_ids: set[int],
        periods: set[str],
        geography_types: set[GeographyType],
        frequency: Frequency,
        concept_id: str,
        unit_id: str,
    ) -> CoverageIndex:
        bits = 0
        for geography_id in geography_ids:
            if geography_id <= 0:
                raise ValueError("geography IDs must be positive")
            bits |= 1 << geography_id
        return cls(
            indicator_variant_id=indicator_variant_id,
            geography_bits=bits,
            periods=frozenset(periods),
            geography_types=frozenset(geography_types),
            frequency=frequency,
            concept_id=concept_id,
            unit_id=unit_id,
        )

    def geography_ids(self) -> tuple[int, ...]:
        remaining = self.geography_bits
        result: list[int] = []
        while remaining:
            lowest_bit = remaining & -remaining
            result.append(lowest_bit.bit_length() - 1)
            remaining ^= lowest_bit
        return tuple(result)


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    status: CompatibilityStatus
    compatibility_class: CompatibilityClass
    geography_bits: int
    periods: tuple[str, ...]
    geography_types: frozenset[GeographyType]
    blockers: tuple[ReasonCode, ...] = field(default_factory=tuple)
    warnings: tuple[ReasonCode, ...] = field(default_factory=tuple)

    @property
    def geography_ids(self) -> tuple[int, ...]:
        return CoverageIndex(
            indicator_variant_id="result",
            geography_bits=self.geography_bits,
            periods=frozenset(self.periods),
            geography_types=self.geography_types or frozenset({GeographyType.COUNTRY}),
            frequency=Frequency.IRREGULAR,
            concept_id="result",
            unit_id="result",
        ).geography_ids()


_OPERATION_ARITY: dict[Operation, tuple[int, int | None]] = {
    Operation.MAP: (1, 1),
    Operation.TREND: (1, None),
    Operation.TABLE: (1, None),
    Operation.SCATTER: (2, 2),
    Operation.RATIO: (2, 2),
    Operation.CORRELATION: (2, None),
}


def operation_arity(operation: Operation) -> tuple[int, int | None]:
    """Return the inclusive indicator-count bounds for an analytical operation."""

    return _OPERATION_ARITY[operation]


def evaluate_compatibility(
    operation: Operation,
    indexes: list[CoverageIndex],
    *,
    convertible_unit_pairs: frozenset[frozenset[str]] = frozenset(),
) -> CompatibilityResult:
    if not indexes:
        return _invalid(ReasonCode.NO_INDICATORS)

    minimum, maximum = _OPERATION_ARITY[operation]
    if len(indexes) < minimum or (maximum is not None and len(indexes) > maximum):
        return _invalid(ReasonCode.OPERATION_ARITY)

    geography_bits = reduce(and_, (index.geography_bits for index in indexes))
    periods = set.intersection(*(set(index.periods) for index in indexes))
    geography_types = set.intersection(*(set(index.geography_types) for index in indexes))

    blockers: list[ReasonCode] = []
    warnings: list[ReasonCode] = []

    if geography_bits == 0:
        blockers.append(ReasonCode.NO_SHARED_GEOGRAPHIES)
    if not periods:
        blockers.append(ReasonCode.NO_SHARED_PERIODS)
    if not geography_types:
        blockers.append(ReasonCode.NO_SHARED_GEOGRAPHY_TYPE)

    frequencies = {index.frequency for index in indexes}
    if len(frequencies) > 1:
        blockers.append(ReasonCode.FREQUENCY_MISMATCH)

    concept_ids = {index.concept_id for index in indexes}
    unit_ids = {index.unit_id for index in indexes}

    compatibility_class = CompatibilityClass.EXACT
    if len(unit_ids) > 1:
        all_pairs_convertible = all(
            frozenset((left, right)) in convertible_unit_pairs
            for left in unit_ids
            for right in unit_ids
            if left != right
        )
        if all_pairs_convertible:
            compatibility_class = CompatibilityClass.CONVERTIBLE
        elif operation is Operation.RATIO:
            blockers.append(ReasonCode.UNIT_MISMATCH)
        else:
            warnings.append(ReasonCode.UNIT_MISMATCH)
            compatibility_class = CompatibilityClass.CONTEXTUAL

    if operation is Operation.RATIO and len(concept_ids) != 2:
        blockers.append(ReasonCode.CONCEPT_MISMATCH)
    elif operation in {Operation.SCATTER, Operation.CORRELATION} and len(concept_ids) > 1:
        warnings.append(ReasonCode.CONTEXTUAL_COMPARISON)
        if compatibility_class is CompatibilityClass.EXACT:
            compatibility_class = CompatibilityClass.CONTEXTUAL

    if blockers:
        return CompatibilityResult(
            status=CompatibilityStatus.INVALID,
            compatibility_class=CompatibilityClass.INCOMPATIBLE,
            geography_bits=geography_bits,
            periods=tuple(sorted(periods)),
            geography_types=frozenset(geography_types),
            blockers=tuple(dict.fromkeys(blockers)),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    return CompatibilityResult(
        status=CompatibilityStatus.WARNING if warnings else CompatibilityStatus.VALID,
        compatibility_class=compatibility_class,
        geography_bits=geography_bits,
        periods=tuple(sorted(periods)),
        geography_types=frozenset(geography_types),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _invalid(reason: ReasonCode) -> CompatibilityResult:
    return CompatibilityResult(
        status=CompatibilityStatus.INVALID,
        compatibility_class=CompatibilityClass.INCOMPATIBLE,
        geography_bits=0,
        periods=(),
        geography_types=frozenset(),
        blockers=(reason,),
    )
