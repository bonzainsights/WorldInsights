import assert from "node:assert/strict";
import test from "node:test";

import {
  countryMatchesSearch,
  countryScopeSummary,
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

test("empty query exposes the complete catalog and unmatched query exposes none", () => {
  assert.equal(countryScopeSummary(countries, "").visibleCount, countries.length);
  assert.equal(countryScopeSummary(countries, "not-a-country").visibleCount, 0);
});
