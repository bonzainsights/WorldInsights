import assert from "node:assert/strict";
import test from "node:test";
import { provenanceHtml } from "../dist/apps/web/src/provenance.js";

const release = {
  kind: "catalog",
  latest: {
    schema_version: 2,
    release_id: "world-bank-indicators-2019-2023-sample",
    catalog: "releases/world-bank-indicators-2019-2023-sample/catalog.json",
    catalog_sha256: "a".repeat(64),
  },
  catalogUrl: new URL("https://example.test/data/releases/world-bank-indicators-2019-2023-sample/catalog.json"),
  catalog: {
    schema_version: 2,
    release: {
      release_id: "world-bank-indicators-2019-2023-sample",
      provider_id: "world-bank",
      dataset_id: "indicators",
      retrieved_at: "2026-07-30T00:00:00+00:00",
      source_checksum: "b".repeat(64),
      pipeline_version: "0.4.0",
    },
    geographies: [],
    indicators: [
      {
        indicator_variant_id: "wb.sp.pop.totl",
        provider_id: "world-bank",
        dataset_id: "indicators",
        provider_indicator_code: "SP.POP.TOTL",
        name: "Population, total",
        concept_id: "population.total",
        unit_id: "people",
        frequency: "annual",
        geography_types: ["country"],
        row_count: 15,
        observations: "indicators/wb.sp.pop.totl/observations.json",
        coverage: "indicators/wb.sp.pop.totl/coverage.json",
      },
      {
        indicator_variant_id: "wb.ny.gdp.pcap.cd",
        provider_id: "world-bank",
        dataset_id: "indicators",
        provider_indicator_code: "NY.GDP.PCAP.CD",
        name: "GDP per capita (current US$)",
        concept_id: "economy.gdp_per_capita",
        unit_id: "current_usd_per_person",
        frequency: "annual",
        geography_types: ["country"],
        row_count: 15,
        observations: "indicators/wb.ny.gdp.pcap.cd/observations.json",
        coverage: "indicators/wb.ny.gdp.pcap.cd/coverage.json",
      },
    ],
    files: {},
  },
};

test("renders immutable release and selected indicator provenance", () => {
  const html = provenanceHtml(release, ["wb.sp.pop.totl", "wb.ny.gdp.pcap.cd"]);
  assert.match(html, /world-bank-indicators-2019-2023-sample/);
  assert.match(html, /2026-07-30T00:00:00\+00:00/);
  assert.match(html, /0\.4\.0/);
  assert.match(html, new RegExp("b".repeat(64)));
  assert.match(html, /SP\.POP\.TOTL/);
  assert.match(html, /NY\.GDP\.PCAP\.CD/);
  assert.match(html, /population\.total/);
  assert.match(html, /economy\.gdp_per_capita/);
  assert.equal((html.match(/<tbody>[\s\S]*?<tr>/g) ?? []).length, 1);
});

test("fails closed for duplicate or unknown selected indicators", () => {
  assert.throws(
    () => provenanceHtml(release, ["wb.sp.pop.totl", "wb.sp.pop.totl"]),
    /must be unique/,
  );
  assert.throws(() => provenanceHtml(release, ["unknown"]), /not in the catalog/);
});

test("escapes provider metadata before rendering", () => {
  const unsafe = {
    ...release,
    catalog: {
      ...release.catalog,
      release: {
        ...release.catalog.release,
        provider_id: "<script>alert(1)</script>",
      },
    },
  };
  const html = provenanceHtml(unsafe, ["wb.sp.pop.totl"]);
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /&lt;script&gt;/);
});
