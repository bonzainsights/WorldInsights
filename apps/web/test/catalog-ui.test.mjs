import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { parseCatalogReleaseV2, parseLatestReleaseV2 } from "../../../packages/contracts/dist/catalog-v2.js";
import {
  catalogExplorerShell,
  compatibilityStatusHtml,
  compatibleObservationHtml,
  scopeControlsHtml,
} from "../dist/apps/web/src/catalog-ui.js";

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

test("catalog shell exposes accessible operation and feature controls", async () => {
  const html = catalogExplorerShell(await releaseFixture());

  assert.match(html, /id="operation-select"/);
  assert.match(html, /Map one feature/);
  assert.match(html, /name="indicators"/);
  assert.match(html, /Load compatible data/);
  assert.match(html, /role="status"/);
});

test("compatibility status explains shared coverage and warnings", () => {
  const html = compatibilityStatusHtml({
    status: "warning",
    compatibility_class: "contextual",
    geography_bits_hex: "0x4",
    geography_ids: [2],
    periods: ["2023"],
    geography_types: ["country"],
    blockers: [],
    warnings: ["contextual_comparison"],
  });

  assert.match(html, /Compatible with important context/);
  assert.match(html, /Shared geographies/);
  assert.match(html, /different concepts/);
});

test("compatible observations align selected feature values by geography and period", async () => {
  const release = await releaseFixture();
  const html = compatibleObservationHtml(release, {
    compatibility: {
      status: "warning",
      compatibility_class: "contextual",
      geography_bits_hex: "0x4",
      geography_ids: [2],
      periods: ["2023"],
      geography_types: ["country"],
      blockers: [],
      warnings: ["contextual_comparison"],
    },
    observations: new Map([
      [
        "wb.sp.pop.totl",
        [{
          release_id: "catalog-test-v2",
          indicator_variant_id: "wb.sp.pop.totl",
          geography_id: 2,
          period_start: "2023-01-01",
          period_end: "2023-12-31",
          period_label: "2023",
          frequency: "annual",
          unit_id: "people",
          status: "observed",
          value: 30_896_590,
          provider_quality_flags: [],
          system_quality_flags: [],
        }],
      ],
      [
        "test.gdp.per.capita",
        [{
          release_id: "catalog-test-v2",
          indicator_variant_id: "test.gdp.per.capita",
          geography_id: 2,
          period_start: "2023-01-01",
          period_end: "2023-12-31",
          period_label: "2023",
          frequency: "annual",
          unit_id: "test_currency_per_person",
          status: "observed",
          value: 20,
          provider_quality_flags: [],
          system_quality_flags: [],
        }],
      ],
    ]),
  });

  assert.match(html, /Nepal/);
  assert.match(html, /30,896,590/);
  assert.match(html, />20</);
  const observationTable = html.match(/<table class="data-table">([\s\S]*?)<\/table>/)?.[1] ?? "";
  assert.equal((observationTable.match(/<tr>/g) ?? []).length, 2);
});


test("scope controls use canonical catalog geography names and shared periods", async () => {
  const release = await releaseFixture();
  const html = scopeControlsHtml(release, {
    status: "valid",
    compatibility_class: "exact",
    geography_bits_hex: "0x6",
    geography_ids: [1, 2],
    periods: ["2023"],
    geography_types: ["country"],
    blockers: [],
    warnings: [],
  });
  assert.match(html, /Germany/);
  assert.match(html, /Nepal/);
  assert.match(html, /scope-geography/);
  assert.match(html, /scope-period/);
});
