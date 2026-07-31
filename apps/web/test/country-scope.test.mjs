import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  countryMatchesSearch,
  countryScopeSummary,
  countrySelectionAfterVisibleAction,
  normalizeCountrySearch,
} from "../dist/apps/web/src/country-scope.js";

const countries = [
  { geographyId: 276, name: "Germany", canonicalCode: "DEU", checked: true },
  { geographyId: 384, name: "Côte d'Ivoire", canonicalCode: "CIV", checked: false },
  { geographyId: 524, name: "Nepal", canonicalCode: "NPL", checked: true },
  { geographyId: 840, name: "United States", canonicalCode: "USA", checked: true },
];

test("normalizes case, whitespace, and diacritics for country search", () => {
  assert.equal(normalizeCountrySearch("  CÔTE  "), "cote");
  assert.equal(countryMatchesSearch("Côte d'Ivoire", "CIV", "cote"), true);
  assert.equal(countryMatchesSearch("Côte d'Ivoire", "CIV", "CIV"), true);
  assert.equal(countryMatchesSearch("Germany", "DEU", "nepal"), false);
});

test("country scope summary reports visible and selected counts independently", () => {
  const summary = countryScopeSummary(countries, "u");

  assert.deepEqual(summary.visibleGeographyIds, [276, 840]);
  assert.equal(summary.visibleCount, 2);
  assert.equal(summary.visibleSelectedCount, 2);
  assert.equal(summary.selectedCount, 3);
  assert.equal(summary.totalCount, 4);
});

test("filtering never removes hidden selections from the selected count", () => {
  const summary = countryScopeSummary(countries, "Nepal");

  assert.deepEqual(summary.visibleGeographyIds, [524]);
  assert.equal(summary.visibleSelectedCount, 1);
  assert.equal(summary.selectedCount, 3);
});

test("visible-only bulk actions preserve hidden country selections", () => {
  assert.deepEqual(
    [...countrySelectionAfterVisibleAction(countries, "Nepal", false)].sort((a, b) => a - b),
    [276, 840],
  );
  assert.deepEqual(
    [...countrySelectionAfterVisibleAction(countries, "cote", true)].sort((a, b) => a - b),
    [276, 384, 524, 840],
  );
});

test("search and counts handle a complete 215-country catalog", () => {
  const globalCatalog = Array.from({ length: 215 }, (_, index) => ({
    geographyId: index + 1,
    name: `Country ${String(index + 1).padStart(3, "0")}`,
    canonicalCode: String(index + 1).padStart(3, "0"),
    checked: index % 2 === 0,
  }));

  const complete = countryScopeSummary(globalCatalog, "");
  assert.equal(complete.totalCount, 215);
  assert.equal(complete.visibleCount, 215);
  assert.equal(complete.selectedCount, 108);
  assert.deepEqual(countryScopeSummary(globalCatalog, "215").visibleGeographyIds, [215]);
});

test("empty query exposes the complete catalog and unmatched query exposes none", () => {
  assert.equal(countryScopeSummary(countries, "").visibleCount, countries.length);
  assert.equal(countryScopeSummary(countries, "not-a-country").visibleCount, 0);
});

test("static build publishes the country scope module and stylesheet", async () => {
  const index = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const build = await readFile(new URL("../scripts/build.mjs", import.meta.url), "utf8");
  const styles = await readFile(new URL("../country-scope.css", import.meta.url), "utf8");

  assert.match(index, /country-scope\.css/);
  assert.match(index, /apps\/web\/src\/country-scope\.js/);
  assert.match(build, /country-scope\.css/);
  assert.match(build, /country scope enhancement/);
  assert.match(styles, /country-scope-toolbar/);
  assert.match(styles, /scope-option\[hidden\]/);
});
