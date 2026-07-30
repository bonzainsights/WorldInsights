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
