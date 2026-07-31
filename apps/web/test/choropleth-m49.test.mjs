import assert from "node:assert/strict";
import test from "node:test";

import {
  choroplethMapHtmlM49,
  m49FromGeographyId,
} from "../dist/apps/web/src/choropleth-m49.js";
import { parseWorldTopology } from "../dist/apps/web/src/choropleth.js";

const topology = parseWorldTopology({
  type: "Topology",
  transform: { scale: [1, 1], translate: [-180, -90] },
  arcs: [
    [[190, 140], [10, 0], [0, 10], [-10, 0], [0, -10]],
    [[260, 115], [8, 0], [0, 6], [-8, 0], [0, -6]],
    [[70, 120], [35, 0], [0, 20], [-35, 0], [0, -20]],
  ],
  objects: {
    countries: {
      type: "GeometryCollection",
      geometries: [
        { type: "Polygon", id: "276", properties: { name: "Germany" }, arcs: [[0]] },
        { type: "Polygon", id: "524", properties: { name: "Nepal" }, arcs: [[1]] },
        { type: "Polygon", id: "840", properties: { name: "United States" }, arcs: [[2]] },
      ],
    },
  },
});

const indicators = [{
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
  coverage: "coverage.json",
}];

const geographies = [
  { geography_id: 276, canonical_code: "DEU", name: "Germany", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
  { geography_id: 524, canonical_code: "NPL", name: "Nepal", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
  { geography_id: 840, canonical_code: "USA", name: "United States", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
];

function observation(geographyId, value, period = "2024") {
  return {
    release_id: "release",
    indicator_variant_id: "population",
    geography_id: geographyId,
    period_start: `${period}-01-01`,
    period_end: `${period}-12-31`,
    period_label: period,
    frequency: "annual",
    unit_id: "people",
    status: value === null ? "missing" : "observed",
    value,
    provider_quality_flags: [],
    system_quality_flags: [],
  };
}

test("formats canonical geography IDs as three-digit M49 codes", () => {
  assert.equal(m49FromGeographyId(4), "004");
  assert.equal(m49FromGeographyId(276), "276");
  assert.equal(m49FromGeographyId(840), "840");
  assert.throws(() => m49FromGeographyId(0), /not a valid M49/);
  assert.throws(() => m49FromGeographyId(1000), /not a valid M49/);
  assert.throws(() => m49FromGeographyId(27.6), /not a valid M49/);
});

test("joins country geometry directly by M49 geography ID", () => {
  const html = choroplethMapHtmlM49(
    indicators,
    geographies,
    new Map([["population", [
      observation(276, 84_000_000),
      observation(524, null),
      observation(840, 340_000_000),
    ]]]),
    topology,
  );

  assert.match(html, /canonical UN M49 IDs/);
  assert.match(html, /Germany, 2024\. Population, total: 84,000,000 people/);
  assert.match(html, /Nepal, 2024\. Population, total: no data/);
  assert.match(html, /United States, 2024\. Population, total: 340,000,000 people/);
  assert.match(html, /class="map-country missing-data"/);
});

test("uses the latest selected period and rejects duplicate rows", () => {
  const html = choroplethMapHtmlM49(
    indicators,
    geographies,
    new Map([["population", [observation(276, 1, "2023"), observation(276, 2, "2024")]]]),
    topology,
  );
  assert.match(html, /latest selected period \(2024\)/);
  assert.doesNotMatch(html, /Germany, 2023/);

  assert.throws(
    () => choroplethMapHtmlM49(
      indicators,
      geographies,
      new Map([["population", [observation(276, 1), observation(276, 2)]]]),
      topology,
    ),
    /duplicate map observation/,
  );
});

test("fails closed for aggregates and non-M49 geography IDs", () => {
  assert.throws(
    () => choroplethMapHtmlM49(
      indicators,
      [{ ...geographies[0], geography_type: "aggregate" }],
      new Map([["population", [observation(276, 1)]]]),
      topology,
    ),
    /must be a country or territory/,
  );

  assert.throws(
    () => choroplethMapHtmlM49(
      indicators,
      [{ ...geographies[0], geography_id: 1000 }],
      new Map([["population", [observation(1000, 1)]]]),
      topology,
    ),
    /not a valid M49/,
  );
});
