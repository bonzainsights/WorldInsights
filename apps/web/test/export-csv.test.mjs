import assert from "node:assert/strict";
import test from "node:test";
import {
  compatibleObservationsCsv,
  csvFileName,
} from "../dist/apps/web/src/export-csv.js";

const release = {
  kind: "catalog",
  latest: { schema_version: 2, release_id: "release", catalog: "catalog.json", catalog_sha256: "a".repeat(64) },
  catalogUrl: new URL("https://example.test/catalog.json"),
  catalog: {
    schema_version: 2,
    release: {
      release_id: "world-bank indicators/2019-2023",
      provider_id: "world-bank",
      dataset_id: "indicators",
      retrieved_at: "2026-07-30T00:00:00+00:00",
      source_checksum: "b".repeat(64),
      pipeline_version: "0.4.0",
    },
    geographies: [
      { geography_id: 1, canonical_code: "DEU", name: "Germany", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
      { geography_id: 2, canonical_code: "NPL", name: "Nepal, Federal Democratic Republic", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
    ],
    indicators: [
      { indicator_variant_id: "population", provider_id: "world-bank", dataset_id: "indicators", provider_indicator_code: "SP.POP.TOTL", name: "Population", concept_id: "population.total", unit_id: "people", frequency: "annual", geography_types: ["country"], row_count: 4, observations: "population.json", coverage: "population-coverage.json" },
      { indicator_variant_id: "gdp", provider_id: "world-bank", dataset_id: "indicators", provider_indicator_code: "NY.GDP.PCAP.CD", name: "GDP per capita", concept_id: "economy.gdp_per_capita", unit_id: "current_usd_per_person", frequency: "annual", geography_types: ["country"], row_count: 4, observations: "gdp.json", coverage: "gdp-coverage.json" },
    ],
    files: {},
  },
};

function observation(indicator, geography, period, value) {
  return {
    release_id: release.catalog.release.release_id,
    indicator_variant_id: indicator,
    geography_id: geography,
    period_start: `${period}-01-01`,
    period_end: `${period}-12-31`,
    period_label: period,
    frequency: "annual",
    unit_id: indicator === "population" ? "people" : "current_usd_per_person",
    status: value === null ? "missing" : "observed",
    value,
    provider_quality_flags: [],
    system_quality_flags: [],
  };
}

test("exports stable wide rows with canonical geography identity", () => {
  const result = {
    operation: "scatter",
    compatibility: { status: "warning", compatibility_class: "contextual", geography_bits_hex: "0x6", geography_ids: [1, 2], periods: ["2022", "2023"], geography_types: ["country"], blockers: [], warnings: ["contextual_comparison"] },
    observations: new Map([
      ["population", [observation("population", 2, "2023", 30), observation("population", 1, "2022", 83), observation("population", 1, "2023", 84)]],
      ["gdp", [observation("gdp", 1, "2023", 55), observation("gdp", 2, "2023", null), observation("gdp", 1, "2022", 50)]],
    ]),
  };
  const csv = compatibleObservationsCsv(release, result);
  assert.equal(csv, [
    "release_id,provider_id,dataset_id,geography_id,geography_code,geography_name,period,population,gdp",
    'world-bank indicators/2019-2023,world-bank,indicators,1,DEU,Germany,2022,83,50',
    'world-bank indicators/2019-2023,world-bank,indicators,1,DEU,Germany,2023,84,55',
    'world-bank indicators/2019-2023,world-bank,indicators,2,NPL,"Nepal, Federal Democratic Republic",2023,30,',
    "",
  ].join("\n"));
});

test("creates a safe deterministic filename", () => {
  assert.equal(csvFileName(release), "world-bank-indicators-2019-2023-observations.csv");
});

test("rejects duplicate observations and unknown catalog identities", () => {
  const duplicate = {
    operation: "table",
    compatibility: { status: "valid", compatibility_class: "exact", geography_bits_hex: "0x2", geography_ids: [1], periods: ["2023"], geography_types: ["country"], blockers: [], warnings: [] },
    observations: new Map([["population", [observation("population", 1, "2023", 84), observation("population", 1, "2023", 85)]]]),
  };
  assert.throws(() => compatibleObservationsCsv(release, duplicate), /duplicate CSV observation/);

  const unknown = { ...duplicate, observations: new Map([["unknown", []]]) };
  assert.throws(() => compatibleObservationsCsv(release, unknown), /not in the catalog/);
});
