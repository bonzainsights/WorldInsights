import json
import zlib
from base64 import urlsafe_b64encode

import pytest

from worldinsights.compatibility import Operation
from worldinsights.recipe import (
    ExplorationRecipe,
    GeographySelection,
    GeographySelectionMode,
    RecipeError,
    TimeSelection,
    TimeSelectionMode,
    TransformSelection,
    Visualization,
    build_exploration_url,
    decode_recipe,
    encode_recipe,
    recipe_from_dict,
    recipe_from_url,
    recipe_to_dict,
)


def sample_recipe() -> ExplorationRecipe:
    return ExplorationRecipe(
        release_id="world-bank-population-2023-sample",
        operation=Operation.SCATTER,
        indicator_variant_ids=("wb.sp.pop.totl", "wb.ny.gdp.pcap.cd"),
        visualization=Visualization.SCATTER,
        geography=GeographySelection(
            mode=GeographySelectionMode.INCLUDE,
            geography_ids=(3, 1),
        ),
        time=TimeSelection(mode=TimeSelectionMode.INCLUDE, periods=("2023", "2022")),
        transforms=(
            TransformSelection(
                transform_id="log10",
                parameters=(("base", 10), ("clamp_zero", True)),
            ),
        ),
    )


def test_recipe_round_trips_through_dict() -> None:
    recipe = sample_recipe()
    payload = recipe_to_dict(recipe)

    assert payload["geography"]["geography_ids"] == [1, 3]
    assert payload["time"]["periods"] == ["2022", "2023"]
    assert list(payload["transforms"][0]["parameters"]) == ["base", "clamp_zero"]
    assert recipe_from_dict(payload) == ExplorationRecipe(
        release_id=recipe.release_id,
        operation=recipe.operation,
        indicator_variant_ids=recipe.indicator_variant_ids,
        visualization=recipe.visualization,
        geography=GeographySelection(
            mode=GeographySelectionMode.INCLUDE,
            geography_ids=(1, 3),
        ),
        time=TimeSelection(
            mode=TimeSelectionMode.INCLUDE,
            periods=("2022", "2023"),
        ),
        transforms=(
            TransformSelection(
                transform_id="log10",
                parameters=(("base", 10), ("clamp_zero", True)),
            ),
        ),
    )


def test_recipe_encoding_is_deterministic_and_url_safe() -> None:
    recipe = sample_recipe()
    first = encode_recipe(recipe)
    second = encode_recipe(recipe)

    assert first == second
    assert "=" not in first
    assert decode_recipe(first) == recipe_from_dict(recipe_to_dict(recipe))


def test_recipe_url_replaces_existing_recipe_and_preserves_other_query_values() -> None:
    recipe = sample_recipe()
    url = build_exploration_url(
        "https://example.test/explore?theme=dark&r=old#chart",
        recipe,
    )

    assert "theme=dark" in url
    assert "r=old" not in url
    assert url.endswith("#chart")
    assert recipe_from_url(url) == recipe_from_dict(recipe_to_dict(recipe))


def test_operation_arity_and_visualization_are_validated() -> None:
    with pytest.raises(RecipeError, match="requires 2 indicators"):
        ExplorationRecipe(
            release_id="release",
            operation=Operation.SCATTER,
            indicator_variant_ids=("one",),
            visualization=Visualization.SCATTER,
        )

    with pytest.raises(RecipeError, match="not valid"):
        ExplorationRecipe(
            release_id="release",
            operation=Operation.MAP,
            indicator_variant_ids=("one",),
            visualization=Visualization.LINE,
        )


def test_selection_modes_reject_ambiguous_payloads() -> None:
    with pytest.raises(RecipeError, match="cannot contain IDs"):
        GeographySelection(
            mode=GeographySelectionMode.ALL_COMPATIBLE,
            geography_ids=(1,),
        )

    with pytest.raises(RecipeError, match="requires at least one period"):
        TimeSelection(mode=TimeSelectionMode.INCLUDE)


def test_recipe_rejects_unknown_fields() -> None:
    payload = recipe_to_dict(sample_recipe())
    payload["unexpected"] = True

    with pytest.raises(RecipeError, match=r"unknown=\['unexpected'\]"):
        recipe_from_dict(payload)


def test_recipe_rejects_invalid_or_oversized_tokens() -> None:
    with pytest.raises(RecipeError, match="invalid recipe token"):
        decode_recipe("not-a-zlib-payload")

    oversized_json = json.dumps({"value": "x" * 70_000}).encode()
    oversized_token = urlsafe_b64encode(zlib.compress(oversized_json)).rstrip(b"=").decode()
    with pytest.raises(RecipeError, match="too large"):
        decode_recipe(oversized_token)


def test_recipe_requires_exactly_one_url_parameter() -> None:
    with pytest.raises(RecipeError, match="exactly one"):
        recipe_from_url("https://example.test/explore")
    with pytest.raises(RecipeError, match="exactly one"):
        recipe_from_url("https://example.test/explore?r=a&r=b")
