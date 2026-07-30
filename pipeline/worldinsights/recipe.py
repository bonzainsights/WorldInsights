"""Versioned, deterministic exploration recipe contracts and URL encoding."""

from __future__ import annotations

import base64
import json
import math
import zlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TypeAlias
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from worldinsights.compatibility import Operation, operation_arity

RECIPE_SCHEMA_VERSION = 1
_MAX_TOKEN_CHARACTERS = 32_768
_MAX_DECOMPRESSED_BYTES = 65_536

JsonScalar: TypeAlias = str | int | float | bool | None


class RecipeError(ValueError):
    """Raised when an exploration recipe is invalid or cannot be decoded."""


class GeographySelectionMode(StrEnum):
    ALL_COMPATIBLE = "all_compatible"
    INCLUDE = "include"


class TimeSelectionMode(StrEnum):
    LATEST = "latest"
    ALL_COMPATIBLE = "all_compatible"
    INCLUDE = "include"


class Visualization(StrEnum):
    MAP = "map"
    LINE = "line"
    TABLE = "table"
    SCATTER = "scatter"
    BAR = "bar"


@dataclass(frozen=True, slots=True)
class GeographySelection:
    mode: GeographySelectionMode = GeographySelectionMode.ALL_COMPATIBLE
    geography_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if any(geography_id <= 0 for geography_id in self.geography_ids):
            raise RecipeError("geography IDs must be positive")
        if len(set(self.geography_ids)) != len(self.geography_ids):
            raise RecipeError("geography IDs must be unique")
        if self.mode is GeographySelectionMode.INCLUDE and not self.geography_ids:
            raise RecipeError("include geography selection requires at least one ID")
        if self.mode is GeographySelectionMode.ALL_COMPATIBLE and self.geography_ids:
            raise RecipeError("all-compatible geography selection cannot contain IDs")

    @property
    def canonical_ids(self) -> tuple[int, ...]:
        return tuple(sorted(self.geography_ids))


@dataclass(frozen=True, slots=True)
class TimeSelection:
    mode: TimeSelectionMode = TimeSelectionMode.LATEST
    periods: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if any(not period.strip() for period in self.periods):
            raise RecipeError("period labels cannot be empty")
        if len(set(self.periods)) != len(self.periods):
            raise RecipeError("period labels must be unique")
        if self.mode is TimeSelectionMode.INCLUDE and not self.periods:
            raise RecipeError("include time selection requires at least one period")
        if self.mode is not TimeSelectionMode.INCLUDE and self.periods:
            raise RecipeError("latest and all-compatible time selections cannot contain periods")

    @property
    def canonical_periods(self) -> tuple[str, ...]:
        return tuple(sorted(self.periods))


@dataclass(frozen=True, slots=True)
class TransformSelection:
    transform_id: str
    parameters: tuple[tuple[str, JsonScalar], ...] = ()

    def __post_init__(self) -> None:
        if not self.transform_id.strip():
            raise RecipeError("transform_id is required")
        names = [name for name, _ in self.parameters]
        if any(not name.strip() for name in names):
            raise RecipeError("transform parameter names cannot be empty")
        if len(set(names)) != len(names):
            raise RecipeError("transform parameter names must be unique")
        for _, value in self.parameters:
            if isinstance(value, float) and not math.isfinite(value):
                raise RecipeError("transform parameter floats must be finite")

    @property
    def canonical_parameters(self) -> tuple[tuple[str, JsonScalar], ...]:
        return tuple(sorted(self.parameters, key=lambda item: item[0]))


_ALLOWED_VISUALIZATIONS: dict[Operation, frozenset[Visualization]] = {
    Operation.MAP: frozenset({Visualization.MAP, Visualization.TABLE}),
    Operation.TREND: frozenset({Visualization.LINE, Visualization.TABLE}),
    Operation.TABLE: frozenset({Visualization.TABLE}),
    Operation.SCATTER: frozenset({Visualization.SCATTER, Visualization.TABLE}),
    Operation.RATIO: frozenset({Visualization.LINE, Visualization.BAR, Visualization.TABLE}),
    Operation.CORRELATION: frozenset({Visualization.SCATTER, Visualization.TABLE}),
}


@dataclass(frozen=True, slots=True)
class ExplorationRecipe:
    release_id: str
    operation: Operation
    indicator_variant_ids: tuple[str, ...]
    visualization: Visualization
    geography: GeographySelection = field(default_factory=GeographySelection)
    time: TimeSelection = field(default_factory=TimeSelection)
    transforms: tuple[TransformSelection, ...] = ()
    schema_version: int = RECIPE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RECIPE_SCHEMA_VERSION:
            raise RecipeError(f"unsupported recipe schema version: {self.schema_version}")
        if not self.release_id.strip():
            raise RecipeError("release_id is required")
        if any(not indicator_id.strip() for indicator_id in self.indicator_variant_ids):
            raise RecipeError("indicator IDs cannot be empty")
        if len(set(self.indicator_variant_ids)) != len(self.indicator_variant_ids):
            raise RecipeError("indicator IDs must be unique")

        minimum, maximum = operation_arity(self.operation)
        count = len(self.indicator_variant_ids)
        if count < minimum or (maximum is not None and count > maximum):
            raise RecipeError(
                f"operation {self.operation.value!r} requires "
                f"{_format_arity(minimum, maximum)} indicators"
            )
        if self.visualization not in _ALLOWED_VISUALIZATIONS[self.operation]:
            raise RecipeError(
                f"visualization {self.visualization.value!r} is not valid for "
                f"operation {self.operation.value!r}"
            )


def recipe_to_dict(recipe: ExplorationRecipe) -> dict[str, Any]:
    """Return a canonical JSON-compatible recipe representation."""

    return {
        "schema_version": recipe.schema_version,
        "release_id": recipe.release_id,
        "operation": recipe.operation.value,
        "indicator_variant_ids": list(recipe.indicator_variant_ids),
        "visualization": recipe.visualization.value,
        "geography": {
            "mode": recipe.geography.mode.value,
            "geography_ids": list(recipe.geography.canonical_ids),
        },
        "time": {
            "mode": recipe.time.mode.value,
            "periods": list(recipe.time.canonical_periods),
        },
        "transforms": [
            {
                "transform_id": transform.transform_id,
                "parameters": {name: value for name, value in transform.canonical_parameters},
            }
            for transform in recipe.transforms
        ],
    }


def recipe_from_dict(payload: object) -> ExplorationRecipe:
    """Validate and construct a recipe from an untrusted JSON-compatible value."""

    root = _expect_object(payload, "recipe")
    _require_exact_keys(
        root,
        {
            "schema_version",
            "release_id",
            "operation",
            "indicator_variant_ids",
            "visualization",
            "geography",
            "time",
            "transforms",
        },
        "recipe",
    )

    geography_payload = _expect_object(root["geography"], "geography")
    _require_exact_keys(geography_payload, {"mode", "geography_ids"}, "geography")
    time_payload = _expect_object(root["time"], "time")
    _require_exact_keys(time_payload, {"mode", "periods"}, "time")

    transform_payloads = _expect_list(root["transforms"], "transforms")
    transforms: list[TransformSelection] = []
    for index, item in enumerate(transform_payloads):
        transform = _expect_object(item, f"transforms[{index}]")
        _require_exact_keys(
            transform,
            {"transform_id", "parameters"},
            f"transforms[{index}]",
        )
        parameters = _expect_object(transform["parameters"], f"transforms[{index}].parameters")
        parameter_items: list[tuple[str, JsonScalar]] = []
        for name, value in parameters.items():
            if not isinstance(name, str):
                raise RecipeError("transform parameter names must be strings")
            if value is not None and not isinstance(value, (str, int, float, bool)):
                raise RecipeError("transform parameter values must be JSON scalars")
            parameter_items.append((name, value))
        transforms.append(
            TransformSelection(
                transform_id=_expect_string(
                    transform["transform_id"], f"transforms[{index}].transform_id"
                ),
                parameters=tuple(parameter_items),
            )
        )

    return ExplorationRecipe(
        schema_version=_expect_int(root["schema_version"], "schema_version"),
        release_id=_expect_string(root["release_id"], "release_id"),
        operation=_parse_enum(Operation, root["operation"], "operation"),
        indicator_variant_ids=tuple(
            _expect_string(value, "indicator_variant_ids[]")
            for value in _expect_list(root["indicator_variant_ids"], "indicator_variant_ids")
        ),
        visualization=_parse_enum(Visualization, root["visualization"], "visualization"),
        geography=GeographySelection(
            mode=_parse_enum(
                GeographySelectionMode, geography_payload["mode"], "geography.mode"
            ),
            geography_ids=tuple(
                _expect_int(value, "geography.geography_ids[]")
                for value in _expect_list(
                    geography_payload["geography_ids"], "geography.geography_ids"
                )
            ),
        ),
        time=TimeSelection(
            mode=_parse_enum(TimeSelectionMode, time_payload["mode"], "time.mode"),
            periods=tuple(
                _expect_string(value, "time.periods[]")
                for value in _expect_list(time_payload["periods"], "time.periods")
            ),
        ),
        transforms=tuple(transforms),
    )


def encode_recipe(recipe: ExplorationRecipe) -> str:
    """Encode a recipe as compact URL-safe text."""

    raw = json.dumps(
        recipe_to_dict(recipe),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    return base64.urlsafe_b64encode(compressed).rstrip(b"=").decode("ascii")


def decode_recipe(token: str) -> ExplorationRecipe:
    """Decode an untrusted URL token with size and schema protections."""

    if not token or len(token) > _MAX_TOKEN_CHARACTERS:
        raise RecipeError("recipe token is empty or too large")
    try:
        padding = "=" * (-len(token) % 4)
        compressed = base64.urlsafe_b64decode(token + padding)
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(compressed, _MAX_DECOMPRESSED_BYTES + 1)
        if len(raw) > _MAX_DECOMPRESSED_BYTES or decompressor.unconsumed_tail:
            raise RecipeError("decoded recipe is too large")
        raw += decompressor.flush()
        if len(raw) > _MAX_DECOMPRESSED_BYTES or not decompressor.eof:
            raise RecipeError("decoded recipe is too large or truncated")
        payload = json.loads(raw.decode("utf-8"))
    except RecipeError:
        raise
    except (ValueError, UnicodeDecodeError, zlib.error) as error:
        raise RecipeError("invalid recipe token") from error
    return recipe_from_dict(payload)


def build_exploration_url(base_url: str, recipe: ExplorationRecipe) -> str:
    """Add or replace the versioned recipe query parameter in a URL."""

    split = urlsplit(base_url)
    query = parse_qs(split.query, keep_blank_values=True)
    query["r"] = [encode_recipe(recipe)]
    return urlunsplit(
        (split.scheme, split.netloc, split.path, urlencode(query, doseq=True), split.fragment)
    )


def recipe_from_url(url: str) -> ExplorationRecipe:
    """Restore exactly one recipe query parameter from a URL."""

    values = parse_qs(urlsplit(url).query, keep_blank_values=True).get("r", [])
    if len(values) != 1:
        raise RecipeError("URL must contain exactly one recipe parameter")
    return decode_recipe(values[0])


def _format_arity(minimum: int, maximum: int | None) -> str:
    if maximum is None:
        return f"at least {minimum}"
    if minimum == maximum:
        return str(minimum)
    return f"between {minimum} and {maximum}"


def _expect_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise RecipeError(f"{field_name} must be an object with string keys")
    return value


def _expect_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise RecipeError(f"{field_name} must be a list")
    return value


def _expect_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise RecipeError(f"{field_name} must be a string")
    return value


def _expect_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RecipeError(f"{field_name} must be an integer")
    return value


def _parse_enum(enum_type: type[StrEnum], value: object, field_name: str) -> Any:
    string_value = _expect_string(value, field_name)
    try:
        return enum_type(string_value)
    except ValueError as error:
        raise RecipeError(f"unsupported {field_name}: {string_value!r}") from error


def _require_exact_keys(value: dict[str, Any], expected: set[str], field_name: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise RecipeError(
            f"{field_name} has invalid fields; missing={missing}, unknown={unknown}"
        )
