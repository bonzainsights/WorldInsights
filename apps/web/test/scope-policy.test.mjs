import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  evaluateOperationScope,
  MAX_TREND_COUNTRIES,
} from "../dist/apps/web/src/scope-policy.js";
import {
  MAX_LABELED_SCATTER_POINTS,
  shouldSuppressScatterLabels,
} from "../dist/apps/web/src/scope-policy-ui.js";

test("map and table operations accept complete global scope", () => {
  assert.equal(evaluateOperationScope("map", 215, 6).valid, true);
  assert.equal(evaluateOperationScope("table", 215, 6).valid, true);
  assert.equal(evaluateOperationScope("ratio", 215, 6).valid, true);
});

test("trend scope is bounded by distinct series styles and requires history", () => {
  assert.equal(MAX_TREND_COUNTRIES, 5);
  assert.equal(evaluateOperationScope("trend", 5, 6).valid, true);

  const tooMany = evaluateOperationScope("trend", 6, 6);
  assert.equal(tooMany.valid, false);
  assert.match(tooMany.messages.join(" "), /at most 5 countries/);

  const tooShort = evaluateOperationScope("trend", 5, 1);
  assert.equal(tooShort.valid, false);
  assert.match(tooShort.messages.join(" "), /at least two periods/);
});

test("scatter and correlation require exactly one period", () => {
  assert.equal(evaluateOperationScope("scatter", 215, 1).valid, true);
  assert.equal(evaluateOperationScope("correlation", 215, 1).valid, true);
  assert.equal(evaluateOperationScope("scatter", 215, 6).valid, false);
  assert.equal(evaluateOperationScope("correlation", 215, 0).valid, false);
});

test("all operations reject empty geography or period scope", () => {
  const policy = evaluateOperationScope("map", 0, 0);
  assert.equal(policy.valid, false);
  assert.match(policy.messages.join(" "), /at least one country/);
  assert.match(policy.messages.join(" "), /at least one period/);
});

test("dense scatter plots suppress only overlapping text labels", () => {
  assert.equal(MAX_LABELED_SCATTER_POINTS, 40);
  assert.equal(shouldSuppressScatterLabels(40), false);
  assert.equal(shouldSuppressScatterLabels(41), true);
  assert.equal(shouldSuppressScatterLabels(215), true);
  assert.throws(() => shouldSuppressScatterLabels(-1), /non-negative integer/);
});

test("explorer evaluates scope policy before observation partitions", async () => {
  const source = await readFile(new URL("../src/explorer.ts", import.meta.url), "utf8");
  const policy = source.indexOf("evaluateOperationScope(");
  const observations = source.indexOf("this.#observations(indicatorId)");

  assert.ok(policy >= 0);
  assert.ok(observations >= 0);
  assert.ok(policy < observations);
  assert.match(source, /scope is unsuitable/);
});

test("static build publishes policy UI and styling", async () => {
  const index = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const build = await readFile(new URL("../scripts/build.mjs", import.meta.url), "utf8");
  const styles = await readFile(new URL("../scope-policy.css", import.meta.url), "utf8");

  assert.match(index, /scope-policy\.css/);
  assert.match(index, /apps\/web\/src\/scope-policy-ui\.js/);
  assert.match(build, /scope-policy\.css/);
  assert.match(build, /chart scope policy guidance/);
  assert.match(styles, /scope-policy-panel/);
  assert.match(styles, /dense-scatter/);
});
