from worldinsights.compatibility import (
    CompatibilityClass,
    CompatibilityStatus,
    CoverageIndex,
    Operation,
    ReasonCode,
    evaluate_compatibility,
)
from worldinsights.contracts import Frequency, GeographyType


def coverage(
    indicator: str,
    geographies: set[int],
    periods: set[str],
    *,
    concept: str = "population",
    unit: str = "people",
) -> CoverageIndex:
    return CoverageIndex.from_geography_ids(
        indicator_variant_id=indicator,
        geography_ids=geographies,
        periods=periods,
        geography_types={GeographyType.COUNTRY},
        frequency=Frequency.ANNUAL,
        concept_id=concept,
        unit_id=unit,
    )


def test_bitset_round_trip() -> None:
    index = coverage("a", {1, 3, 100}, {"2024"})

    assert index.geography_ids() == (1, 3, 100)


def test_shared_coverage_uses_intersection() -> None:
    result = evaluate_compatibility(
        Operation.SCATTER,
        [
            coverage("population", {1, 2, 3}, {"2022", "2023", "2024"}),
            coverage("gdp", {2, 3, 4}, {"2021", "2023", "2024"}, concept="gdp", unit="usd"),
        ],
    )

    assert result.geography_ids == (2, 3)
    assert result.periods == ("2023", "2024")
    assert result.status is CompatibilityStatus.WARNING
    assert ReasonCode.CONTEXTUAL_COMPARISON in result.warnings


def test_no_shared_geography_fails_before_querying_observations() -> None:
    result = evaluate_compatibility(
        Operation.SCATTER,
        [
            coverage("a", {1}, {"2024"}),
            coverage("b", {2}, {"2024"}, concept="gdp"),
        ],
    )

    assert result.status is CompatibilityStatus.INVALID
    assert ReasonCode.NO_SHARED_GEOGRAPHIES in result.blockers


def test_no_shared_period_fails() -> None:
    result = evaluate_compatibility(
        Operation.SCATTER,
        [
            coverage("a", {1}, {"2023"}),
            coverage("b", {1}, {"2024"}, concept="gdp"),
        ],
    )

    assert ReasonCode.NO_SHARED_PERIODS in result.blockers


def test_operation_arity_is_enforced() -> None:
    result = evaluate_compatibility(Operation.MAP, [coverage("a", {1}, {"2024"}), coverage("b", {1}, {"2024"})])

    assert result.blockers == (ReasonCode.OPERATION_ARITY,)


def test_convertible_units_are_accepted() -> None:
    result = evaluate_compatibility(
        Operation.SCATTER,
        [
            coverage("a", {1}, {"2024"}, unit="usd"),
            coverage("b", {1}, {"2024"}, unit="usd-thousands"),
        ],
        convertible_unit_pairs=frozenset({frozenset({"usd", "usd-thousands"})}),
    )

    assert result.status is CompatibilityStatus.VALID
    assert result.compatibility_class is CompatibilityClass.CONVERTIBLE


def test_ratio_rejects_unregistered_unit_relationship() -> None:
    result = evaluate_compatibility(
        Operation.RATIO,
        [
            coverage("a", {1}, {"2024"}, concept="gdp", unit="usd"),
            coverage("b", {1}, {"2024"}, concept="population", unit="people"),
        ],
    )

    assert result.status is CompatibilityStatus.INVALID
    assert ReasonCode.UNIT_MISMATCH in result.blockers
