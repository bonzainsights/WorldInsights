import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { parseCoverageManifestV1 } from "../../contracts/dist/index.js";
import {
  convertibleUnitPairKey,
  evaluateCoverageCompatibility,
  geographyIdsFromBits,
} from "../dist/packages/compatibility/src/index.js";

const root = new URL(
  "../../../tests/fixtures/contracts/catalog-release-v2/releases/catalog-test-v2/indicators/",
  import.meta.url,
);

async function coverage(indicatorId) {
  return parseCoverageManifestV1(
    JSON.parse(await readFile(new URL(`${indicatorId}/coverage.json`, root), "utf8")),
  );
}

test("intersects geography and period coverage without observations", async () => {
  const population = await coverage("wb.sp.pop.totl");
  const synthetic = await coverage("test.gdp.per.capita");
  const result = evaluateCoverageCompatibility("scatter", [population, synthetic]);

  assert.equal(result.status, "warning");
  assert.deepEqual(result.geography_ids, [2]);
  assert.deepEqual(result.periods, ["2023"]);
  assert.deepEqual(result.geography_types, ["country"]);
  assert.deepEqual(result.warnings, ["unit_mismatch", "contextual_comparison"]);
});

test("blocks dimensionally unregistered ratios", async () => {
  const population = await coverage("wb.sp.pop.totl");
  const synthetic = await coverage("test.gdp.per.capita");
  const result = evaluateCoverageCompatibility("ratio", [population, synthetic]);

  assert.equal(result.status, "invalid");
  assert.deepEqual(result.blockers, ["unit_mismatch"]);
});

test("recognizes registered convertible units", () => {
  const left = {
    indicator_variant_id: "left",
    geography_bits_hex: "0x6",
    geography_ids: [1, 2],
    periods: ["2023"],
    geography_types: ["country"],
    frequency: "annual",
    concept_id: "temperature",
    unit_id: "celsius",
  };
  const right = { ...left, indicator_variant_id: "right", unit_id: "fahrenheit" };
  const pairs = new Set([convertibleUnitPairKey("celsius", "fahrenheit")]);
  const result = evaluateCoverageCompatibility("trend", [left, right], pairs);

  assert.equal(result.status, "valid");
  assert.equal(result.compatibility_class, "convertible");
});

test("reports operation arity and empty intersections", () => {
  const index = {
    indicator_variant_id: "one",
    geography_bits_hex: "0x2",
    geography_ids: [1],
    periods: ["2023"],
    geography_types: ["country"],
    frequency: "annual",
    concept_id: "one",
    unit_id: "one",
  };
  assert.deepEqual(
    evaluateCoverageCompatibility("scatter", [index]).blockers,
    ["operation_arity"],
  );

  const disjoint = {
    ...index,
    indicator_variant_id: "two",
    geography_bits_hex: "0x4",
    geography_ids: [2],
    periods: ["2022"],
    concept_id: "two",
  };
  const result = evaluateCoverageCompatibility("scatter", [index, disjoint]);
  assert.ok(result.blockers.includes("no_shared_geographies"));
  assert.ok(result.blockers.includes("no_shared_periods"));
});

test("requires exactly two indicators for browser correlation", () => {
  const first = {
    indicator_variant_id: "one",
    geography_bits_hex: "0x2",
    geography_ids: [1],
    periods: ["2023"],
    geography_types: ["country"],
    frequency: "annual",
    concept_id: "shared",
    unit_id: "shared",
  };
  const second = { ...first, indicator_variant_id: "two" };
  const third = { ...first, indicator_variant_id: "three" };

  assert.deepEqual(
    evaluateCoverageCompatibility("correlation", [first]).blockers,
    ["operation_arity"],
  );

  const accepted = evaluateCoverageCompatibility("correlation", [first, second]);
  assert.equal(accepted.status, "valid");
  assert.deepEqual(accepted.blockers, []);

  assert.deepEqual(
    evaluateCoverageCompatibility("correlation", [first, second, third]).blockers,
    ["operation_arity"],
  );
});

test("decodes compact coverage bitsets", () => {
  assert.deepEqual(geographyIdsFromBits(0xen), [1, 2, 3]);
  assert.throws(() => geographyIdsFromBits(-1n), RangeError);
});
