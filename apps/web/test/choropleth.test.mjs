import assert from "node:assert/strict";
import test from "node:test";

import {
  WORLD_ATLAS_URL,
  choroplethMapHtml,
  geometryPath,
  parseWorldTopology,
} from "../dist/apps/web/src/choropleth.js";

const topologyFixture = {
  type: "Topology",
  transform: { scale: [1, 1], translate: [-180, -90] },
  arcs: [
    [[190, 140], [10, 0], [0, 10], [-10, 0], [0, -10]],
    [[260, 115], [8, 0], [0, 6], [-8, 0], [0, -6]],
    [[70, 120], [35, 0], [0, 20], [-35, 0], [0, -20]],
    [[130, 100], [10, 0], [0, 10], [-10, 0], [0, -10]],
  ],
  objects: {
    countries: {
      type: "GeometryCollection",
      geometries: [
        { type: "Polygon", id: "276", properties: { name: "Germany" }, arcs: [[0]] },
        { type: "Polygon", id: "524", properties: { name: "Nepal" }, arcs: [[1]] },
        { type: "Polygon", id: "840", properties: { name: "United States" }, arcs: [[2]] },
        { type: "Polygon", id: "999", properties: { name: "Background" }, arcs: [[3]] },
      ],
    },
  },
};

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
  row_count: 6,
  observations: "population.json",
  coverage: "coverage.json",
}];

const geographies = [
  { geography_id: 1, canonical_code: "DEU", name: "Germany", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
  { geography_id: 2, canonical_code: "NPL", name: "Nepal", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
  { geography_id: 3, canonical_code: "USA", name: "United States", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
];

function observation(geographyId, period, value) {
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

test("parses a strict TopoJSON country collection", () => {
  const topology = parseWorldTopology(topologyFixture);
  assert.equal(topology.objects.countries.geometries.length, 4);
  assert.equal(topology.objects.countries.geometries[0].id, "276");
  assert.throws(
    () => parseWorldTopology({ ...topologyFixture, type: "FeatureCollection" }),
    /must be Topology/,
  );
});

test("decodes delta arcs and supports reversed TopoJSON references", () => {
  const topology = parseWorldTopology(topologyFixture);
  const forward = geometryPath(topology, topology.objects.countries.geometries[0]);
  const reversedGeometry = { ...topology.objects.countries.geometries[0], arcs: [[-1]] };
  const reversed = geometryPath(topology, reversedGeometry);
  assert.match(forward, /^M/);
  assert.match(forward, /Z$/);
  assert.notEqual(forward, reversed);
});

test("renders the latest selected period with accessible exact values", () => {
  const topology = parseWorldTopology(topologyFixture);
  const html = choroplethMapHtml(
    indicators,
    geographies,
    new Map([["population", [
      observation(1, "2022", 10),
      observation(1, "2023", 20),
      observation(2, "2023", null),
      observation(3, "2023", 40),
    ]]]),
    topology,
  );
  assert.match(html, /Country choropleth/);
  assert.match(html, /latest selected period \(2023\)/);
  assert.match(html, /Germany, 2023\. Population, total: 20 people/);
  assert.match(html, /United States, 2023\. Population, total: 40 people/);
  assert.match(html, /Nepal, 2023\. Population, total: no data/);
  assert.match(html, /class="map-country missing-data"/);
  assert.match(html, /class="map-country no-coverage"/);
  assert.doesNotMatch(html, /Germany, 2022/);
});

test("fails closed for duplicate or unregistered country observations", () => {
  const topology = parseWorldTopology(topologyFixture);
  assert.throws(
    () => choroplethMapHtml(
      indicators,
      geographies,
      new Map([["population", [observation(1, "2023", 1), observation(1, "2023", 2)]]]),
      topology,
    ),
    /duplicate map observation/,
  );
  assert.throws(
    () => choroplethMapHtml(
      indicators,
      [{ ...geographies[0], geography_id: 9, canonical_code: "XXX" }],
      new Map([["population", [observation(9, "2023", 1)]]]),
      topology,
    ),
    /geometry is not registered/,
  );
});

test("uses a version-pinned geometry source and keeps a table fallback", () => {
  assert.equal(
    WORLD_ATLAS_URL,
    "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json",
  );
  const html = choroplethMapHtml(
    indicators,
    geographies,
    new Map([["population", [observation(1, "2023", 20)]]]),
    parseWorldTopology(topologyFixture),
  );
  assert.match(html, /world-atlas 2\.0\.2/);
  assert.match(html, /Natural Earth 1:110m/);
  assert.match(html, /table remains the authoritative accessible fallback/);
});
