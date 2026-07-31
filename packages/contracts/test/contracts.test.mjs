import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  ContractError,
  parseCoverageManifestV1,
  parseExplorationRecipeV1,
  parseLatestReleaseV1,
  parseObservationsV1,
  parseReleaseManifestV1,
} from "../dist/index.js";
import {
  parseCatalogReleaseV2,
  parseLatestRelease,
  parseLatestReleaseV2,
} from "../dist/catalog-v2.js";

const fixturesRoot = new URL("../../../tests/fixtures/contracts/", import.meta.url);

async function fixture(name) {
  return JSON.parse(await readFile(new URL(name, fixturesRoot), "utf8"));
}

test("parses the Python-generated exploration recipe fixture", async () => {
  const recipe = parseExplorationRecipeV1(await fixture("exploration_recipe_v1.json"));
  assert.equal(recipe.schema_version, 1);
  assert.deepEqual(recipe.geography.geography_ids, [1, 3]);
  assert.deepEqual(recipe.time.periods, ["2022", "2023"]);
});

test("parses the Python-generated static release fixture", async () => {
  const bundle = await fixture("static_release_v1.json");
  const latest = parseLatestReleaseV1(bundle.latest);
  const manifest = parseReleaseManifestV1(bundle.manifest);
  const coverage = parseCoverageManifestV1(bundle.coverage);
  const observations = parseObservationsV1(bundle.observations);

  assert.equal(latest.release_id, manifest.release.release_id);
  assert.equal(manifest.row_count, observations.length);
  assert.deepEqual(coverage.geography_ids, [1, 2, 3]);
  assert.ok(observations.every((row) => row.status === "observed"));
});

test("rejects unknown fields and invalid missing-value semantics", async () => {
  const recipe = await fixture("exploration_recipe_v1.json");
  assert.throws(
    () => parseExplorationRecipeV1({ ...recipe, unexpected: true }),
    ContractError,
  );

  const bundle = await fixture("static_release_v1.json");
  const invalid = structuredClone(bundle.observations);
  invalid[0].status = "missing";
  assert.throws(() => parseObservationsV1(invalid), /must not contain a value/);
});

test("matches Python operation and visualization validation", async () => {
  const recipe = await fixture("exploration_recipe_v1.json");
  assert.throws(
    () =>
      parseExplorationRecipeV1({
        ...recipe,
        indicator_variant_ids: ["one"],
      }),
    /invalid indicator arity/,
  );
  assert.throws(
    () =>
      parseExplorationRecipeV1({
        ...recipe,
        operation: "map",
        indicator_variant_ids: ["one"],
        visualization: "line",
      }),
    /not valid/,
  );
});

test("requires exactly two indicators for correlation recipes", async () => {
  const recipe = await fixture("exploration_recipe_v1.json");
  const correlationRecipe = {
    ...recipe,
    operation: "correlation",
    visualization: "scatter",
  };

  assert.throws(
    () =>
      parseExplorationRecipeV1({
        ...correlationRecipe,
        indicator_variant_ids: ["one"],
      }),
    /invalid indicator arity/,
  );

  const accepted = parseExplorationRecipeV1({
    ...correlationRecipe,
    indicator_variant_ids: ["one", "two"],
  });
  assert.deepEqual(accepted.indicator_variant_ids, ["one", "two"]);

  assert.throws(
    () =>
      parseExplorationRecipeV1({
        ...correlationRecipe,
        indicator_variant_ids: ["one", "two", "three"],
      }),
    /invalid indicator arity/,
  );
});


test("parses the Python-generated V2 catalog fixture", async () => {
  const root = new URL("../../../tests/fixtures/contracts/catalog-release-v2/", import.meta.url);
  const latest = parseLatestReleaseV2(
    JSON.parse(await readFile(new URL("latest.json", root), "utf8")),
  );
  const catalog = parseCatalogReleaseV2(
    JSON.parse(await readFile(new URL(latest.catalog, root), "utf8")),
  );

  assert.equal(parseLatestRelease(latest).schema_version, 2);
  assert.equal(catalog.release.release_id, latest.release_id);
  assert.deepEqual(
    catalog.geographies.map((geography) => geography.canonical_code),
    ["DEU", "NPL", "USA"],
  );
  assert.deepEqual(
    catalog.indicators.map((indicator) => indicator.indicator_variant_id),
    ["test.gdp.per.capita", "wb.sp.pop.totl"],
  );
  assert.ok(catalog.indicators.every((indicator) => catalog.files[indicator.coverage]));
});

test("rejects unsafe or undeclared V2 catalog asset paths", async () => {
  const root = new URL("../../../tests/fixtures/contracts/catalog-release-v2/", import.meta.url);
  const latest = JSON.parse(await readFile(new URL("latest.json", root), "utf8"));
  const catalog = JSON.parse(await readFile(new URL(latest.catalog, root), "utf8"));

  const unsafe = structuredClone(catalog);
  unsafe.indicators[0].coverage = "../outside.json";
  assert.throws(() => parseCatalogReleaseV2(unsafe), /safe relative asset path/);

  const undeclared = structuredClone(catalog);
  delete undeclared.files[undeclared.indicators[0].coverage];
  assert.throws(() => parseCatalogReleaseV2(undeclared), /undeclared file/);

  const invalidParent = structuredClone(catalog);
  invalidParent.geographies[0].parent_id = 99;
  assert.throws(() => parseCatalogReleaseV2(invalidParent), /parent is not declared/);
});
