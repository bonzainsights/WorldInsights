from datetime import date, datetime, timezone

import pytest

from worldinsights.contracts import (
    DataRelease,
    Frequency,
    Geography,
    GeographyType,
    Observation,
    ObservationStatus,
    Period,
    Unit,
)


def test_annual_period_has_explicit_bounds() -> None:
    period = Period.annual(2024)

    assert period.start == date(2024, 1, 1)
    assert period.end == date(2024, 12, 31)
    assert period.frequency is Frequency.ANNUAL


def test_geography_cannot_parent_itself() -> None:
    with pytest.raises(ValueError, match="own parent"):
        Geography(1, "DEU", "Germany", GeographyType.COUNTRY, parent_id=1)


def test_zero_is_a_valid_observed_value() -> None:
    observation = Observation(
        release_id="release-1",
        indicator_variant_id="provider.feature",
        geography_id=1,
        period=Period.annual(2024),
        unit_id="count",
        status=ObservationStatus.OBSERVED,
        value=0.0,
    )

    assert observation.value == 0.0


def test_missing_observation_cannot_hide_a_numeric_value() -> None:
    with pytest.raises(ValueError, match="must not contain"):
        Observation(
            release_id="release-1",
            indicator_variant_id="provider.feature",
            geography_id=1,
            period=Period.annual(2024),
            unit_id="count",
            status=ObservationStatus.MISSING,
            value=0.0,
        )


def test_observed_observation_requires_a_value() -> None:
    with pytest.raises(ValueError, match="require a value"):
        Observation(
            release_id="release-1",
            indicator_variant_id="provider.feature",
            geography_id=1,
            period=Period.annual(2024),
            unit_id="count",
            status=ObservationStatus.OBSERVED,
            value=None,
        )


def test_release_timestamp_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        DataRelease(
            release_id="release-1",
            provider_id="world-bank",
            dataset_id="indicators",
            retrieved_at=datetime(2024, 1, 1),
            source_checksum="abc",
            pipeline_version="0.1.0",
        )


def test_unit_scale_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        Unit("bad", "Bad unit", "x", "count", scale=0)


def test_release_accepts_utc_timestamp() -> None:
    release = DataRelease(
        release_id="release-1",
        provider_id="world-bank",
        dataset_id="indicators",
        retrieved_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        source_checksum="abc",
        pipeline_version="0.1.0",
    )

    assert release.retrieved_at.tzinfo is timezone.utc
