import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  parseCatalogReleaseV2,
  parseLatestReleaseV2,
} from "../../../packages/contracts/dist/catalog-v2.js";
import { compatibleObservationHtml } from "../dist/apps/web/src/catalog-ui.js";

async function releaseFixture() {
  const root = new URL("../../../tests/fixtures/contracts/catalog-release-v2/", import.meta.url);
  const latest = parseLatestReleaseV2(
    JSON.parse(await readFile(new URL("latest.json", root), "utf8")),
  );
  const catalogUrl = new URL(latest.catalog, root);
  const catalog = parseCatalogReleaseV2(
    JSON.parse(await readFile(catalogUrl, "utf8")),
  );
  return { kind: "catalog", latest, catalog, catalogUrl };
}

function observation(indicator, geography, value, unit) {
  return {
    release_id: "catalog-test-v2",
    indicator_variant_id: indicator,
    geography_id: geography,
    period_start: "2023-01-01",
    period_end: "2023-12-31",
    period_label: "2023",
    frequency: "annual",
    unit_id: unit,
    status: "observed",
    value,
    provider_quality_flags: [],
    system_quality_flags: [],
  };
}

function compatibleResult(operation) {
  return {
    operation,
    compatibility: {
      status: "warning",
      compatibility_class: "contextual",
      geography_bits_hex: "0x6",
      geography_ids: [1, 2],
      periods: ["2023"],
      geography_types: ["country"],
      blockers: [],
      warnings: ["contextual_comparison"],
    },
    observations: new Map([
      [
        "test.gdp.per.capita",
        [
          observation("test.gdp.per.capita", 1, 1, "test_currency_per_person"),
          observation("test.gdp.per.capita", 2, 2, "test_currency_per_person"),
        ],
      ],
      [
        "wb.sp.pop.totl",
        [
          observation("wb.sp.pop.totl", 1, 10, "people"),
          observation("wb.sp.pop.totl", 2, 20, "people"),
        ],
      ],
    ]),
  };
}

test("correlation operation renders a coefficient before the scatter plot", async () => {
  const html = compatibleObservationHtml(
    await releaseFixture(),
    compatibleResult("correlation"),
  );

  assert.match(html, /Pearson correlation/);
  assert.match(html, /r = 1\.000/);
  assert.match(html, /2 complete pairs/);
  assert.match(html, /class="scatter-chart"/);
  assert.ok(html.indexOf("Pearson correlation") < html.indexOf("scatter-chart"));
});

test("ordinary scatter remains a visual comparison without a coefficient", async () => {
  const html = compatibleObservationHtml(
    await releaseFixture(),
    compatibleResult("scatter"),
  );

  assert.match(html, /class="scatter-chart"/);
  assert.doesNotMatch(html, /Pearson correlation/);
  assert.doesNotMatch(html, /r = 1\.000/);
});
