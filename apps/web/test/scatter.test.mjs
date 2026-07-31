import assert from "node:assert/strict";
import test from "node:test";
import {
  alignScatterPoints,
  scatterPlotHtml,
} from "../dist/apps/web/src/scatter.js";

const indicators = [
  {
    indicator_variant_id: "population",
    provider_id: "world-bank",
    dataset_id: "indicators",
    provider_indicator_code: "SP.POP.TOTL",
    name: "Population, total",
    concept_id: "population.total",
    unit_id: "people",
    frequency: "annual",
    geography_types: ["country"],
    row_count: 3,
    observations: "population.json",
    coverage: "population-coverage.json",
  },
  {
    indicator_variant_id: "gdp",
    provider_id: "world-bank",
    dataset_id: "indicators",
    provider_indicator_code: "NY.GDP.PCAP.CD",
    name: "GDP per capita (current US$)",
    concept_id: "economy.gdp_per_capita",
    unit_id: "current_usd_per_person",
    frequency: "annual",
    geography_types: ["country"],
    row_count: 3,
    observations: "gdp.json",
    coverage: "gdp-coverage.json",
  },
];

const geographies = [
  { geography_id: 1, canonical_code: "DEU", name: "Germany", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
  { geography_id: 2, canonical_code: "NPL", name: "Nepal", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
  { geography_id: 3, canonical_code: "USA", name: "United States", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
];

function observation(indicator, geography, value, period = "2023") {
  return {
    release_id: "release",
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

test("aligns only complete non-missing country-period pairs", () => {
  const rows = new Map([
    ["population", [observation("population", 1, 83), observation("population", 2, 31), observation("population", 3, null)]],
    ["gdp", [observation("gdp", 1, 55), observation("gdp", 2, 1.4), observation("gdp", 3, 83)]],
  ]);
  assert.deepEqual(alignScatterPoints(rows, "population", "gdp"), [
    { geography_id: 1, period: "2023", x: 83, y: 55 },
    { geography_id: 2, period: "2023", x: 31, y: 1.4 },
  ]);
});

test("rejects duplicate observations instead of choosing one silently", () => {
  const rows = new Map([
    ["population", [observation("population", 1, 83), observation("population", 1, 84)]],
    ["gdp", [observation("gdp", 1, 55)]],
  ]);
  assert.throws(() => alignScatterPoints(rows, "population", "gdp"), /duplicate scatter observation/);
});

test("renders accessible SVG labels and a non-causal warning", () => {
  const rows = new Map([
    ["population", [observation("population", 1, 83), observation("population", 2, 31)]],
    ["gdp", [observation("gdp", 1, 55), observation("gdp", 2, 1.4)]],
  ]);
  const html = scatterPlotHtml(indicators, geographies, rows);
  assert.match(html, /role="img"/);
  assert.match(html, /Germany, 2023/);
  assert.match(html, /Nepal, 2023/);
  assert.match(html, /2 complete pairs/);
  assert.match(html, /does not imply causation/);
});

test("states explicitly when no complete pairs exist", () => {
  const rows = new Map([
    ["population", [observation("population", 1, null)]],
    ["gdp", [observation("gdp", 1, 55)]],
  ]);
  const html = scatterPlotHtml(indicators, geographies, rows);
  assert.match(html, /No complete country-period pairs/);
  assert.match(html, /not converted to zero/);
});
