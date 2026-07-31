import assert from "node:assert/strict";
import test from "node:test";

import {
  correlationSummaryHtml,
  pearsonCorrelation,
} from "../dist/apps/web/src/correlation.js";

function points(xs, ys) {
  return xs.map((x, index) => ({ x, y: ys[index] }));
}

test("calculates perfect positive and negative Pearson correlations", () => {
  const positive = pearsonCorrelation(points(
    [1_000_000_000_001, 1_000_000_000_002, 1_000_000_000_003],
    [4, 8, 12],
  ));
  const negative = pearsonCorrelation(points([1, 2, 3, 4], [8, 6, 4, 2]));

  assert.equal(positive.status, "defined");
  assert.equal(positive.coefficient, 1);
  assert.equal(negative.status, "defined");
  assert.equal(negative.coefficient, -1);
});

test("calculates a non-trivial coefficient from centered complete pairs", () => {
  const result = pearsonCorrelation(points([1, 2, 3, 4], [2, 1, 5, 7]));

  assert.equal(result.status, "defined");
  assert.equal(result.pair_count, 4);
  assert.ok(Math.abs(result.coefficient - 0.8907337387831413) < 1e-12);
});

test("reports insufficient complete pairs instead of inventing a coefficient", () => {
  assert.deepEqual(pearsonCorrelation([]), {
    status: "insufficient_pairs",
    pair_count: 0,
    coefficient: null,
  });
  assert.deepEqual(pearsonCorrelation([{ x: 2, y: 5 }]), {
    status: "insufficient_pairs",
    pair_count: 1,
    coefficient: null,
  });
});

test("reports every constant axis when variance is zero", () => {
  assert.deepEqual(pearsonCorrelation(points([4, 4, 4], [1, 2, 3])), {
    status: "zero_variance",
    pair_count: 3,
    coefficient: null,
    constant_axes: ["x"],
  });
  assert.deepEqual(pearsonCorrelation(points([4, 4], [9, 9])), {
    status: "zero_variance",
    pair_count: 2,
    coefficient: null,
    constant_axes: ["x", "y"],
  });
});

test("fails closed for non-finite input", () => {
  assert.throws(
    () => pearsonCorrelation([{ x: Number.POSITIVE_INFINITY, y: 1 }]),
    /finite x and y values/,
  );
  assert.throws(
    () => pearsonCorrelation([{ x: 1, y: 2 }, { x: Number.NaN, y: 3 }]),
    /finite x and y values/,
  );
});

test("renders an accessible coefficient, pair count, and non-causal warning", () => {
  const html = correlationSummaryHtml(
    points([1, 2, 3, 4], [2, 1, 5, 7]),
    "GDP <per capita>",
    "Life expectancy",
  );

  assert.match(html, /Pearson correlation/);
  assert.match(html, /r = 0\.891/);
  assert.match(html, /Complete pairs/);
  assert.match(html, />4</);
  assert.match(html, /positive linear association/);
  assert.match(html, /does not imply causation/);
  assert.match(html, /GDP &lt;per capita&gt;/);
  assert.doesNotMatch(html, /GDP <per capita>/);
});

test("explains why an undefined coefficient cannot be reported", () => {
  const insufficient = correlationSummaryHtml([{ x: 1, y: 2 }], "X", "Y");
  const constant = correlationSummaryHtml(points([3, 3, 3], [1, 2, 3]), "Constant X", "Y");

  assert.match(insufficient, /At least two complete pairs are required/);
  assert.match(insufficient, /1 is available/);
  assert.match(constant, /Constant X has no variation/);
  assert.match(constant, /requires variation on both axes/);
});
