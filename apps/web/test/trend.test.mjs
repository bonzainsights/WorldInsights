import assert from "node:assert/strict";
import test from "node:test";
import {
  buildTrendSeries,
  trendChartHtml,
} from "../dist/apps/web/src/trend.js";

const indicator = {
  indicator_variant_id: "population",
  provider_id: "world-bank",
  dataset_id: "indicators",
  provider_indicator_code: "SP.POP.TOTL",
  name: "Population, total",
  concept_id: "population.total",
  unit_id: "people",
  frequency: "annual",
  geography_types: ["country"],
  row_count: 15,
  observations: "population.json",
  coverage: "population-coverage.json",
};

const geographies = [
  { geography_id: 1, canonical_code: "DEU", name: "Germany", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
  { geography_id: 2, canonical_code: "NPL", name: "Nepal", geography_type: "country", parent_id: null, valid_from: null, valid_to: null },
];

function observation(geography, period, value) {
  return {
    release_id: "release",
    indicator_variant_id: "population",
    geography_id: geography,
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

test("sorts country series and splits lines at missing years", () => {
  const series = buildTrendSeries([
    observation(1, "2023", 103),
    observation(1, "2019", 99),
    observation(1, "2020", 100),
    observation(1, "2021", null),
    observation(1, "2022", 102),
  ]);
  assert.deepEqual(series, [{
    geography_id: 1,
    points: [
      { period: "2019", value: 99 },
      { period: "2020", value: 100 },
      { period: "2022", value: 102 },
      { period: "2023", value: 103 },
    ],
    segments: [
      [{ period: "2019", value: 99 }, { period: "2020", value: 100 }],
      [{ period: "2022", value: 102 }, { period: "2023", value: 103 }],
    ],
  }]);
});

test("rejects duplicate country-period observations", () => {
  assert.throws(
    () => buildTrendSeries([observation(1, "2023", 103), observation(1, "2023", 104)]),
    /duplicate trend observation/,
  );
});

test("renders accessible country lines and exact point labels", () => {
  const rows = new Map([["population", [
    observation(1, "2019", 83_000_000),
    observation(1, "2020", 83_100_000),
    observation(2, "2019", 28_400_000),
    observation(2, "2020", 28_900_000),
  ]] ]);
  const html = trendChartHtml([indicator], geographies, rows);
  assert.match(html, /role="img"/);
  assert.match(html, /Germany, 2019/);
  assert.match(html, /Nepal, 2020/);
  assert.match(html, /2019–2020/);
  assert.match(html, /Missing values create line gaps/);
  assert.equal((html.match(/<polyline/g) ?? []).length, 2);
});

test("does not pretend multiple indicators share one trend axis", () => {
  const html = trendChartHtml([indicator], geographies, new Map([
    ["population", [observation(1, "2023", 103)]],
    ["other", [observation(1, "2023", 5)]],
  ]));
  assert.match(html, /Select exactly one feature/);
});
