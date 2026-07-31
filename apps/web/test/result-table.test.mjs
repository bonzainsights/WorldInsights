import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  DEFAULT_RESULT_PAGE_SIZE,
  nextVisibleRowCount,
  resultTablePageState,
} from "../dist/apps/web/src/result-table.js";

test("global 1,290-row results begin with a bounded accessible page", () => {
  const state = resultTablePageState(1290, DEFAULT_RESULT_PAGE_SIZE);

  assert.equal(DEFAULT_RESULT_PAGE_SIZE, 100);
  assert.deepEqual(state, {
    totalRows: 1290,
    visibleRows: 100,
    remainingRows: 1190,
    complete: false,
  });
});

test("show-more increments are deterministic and clamp at the total", () => {
  assert.equal(nextVisibleRowCount(1290, 100), 200);
  assert.equal(nextVisibleRowCount(1290, 1200), 1290);
  assert.equal(nextVisibleRowCount(80, 80), 80);
  assert.equal(nextVisibleRowCount(250, 100, 25), 125);
});

test("page state clamps requests and recognizes complete tables", () => {
  assert.deepEqual(resultTablePageState(42, 100), {
    totalRows: 42,
    visibleRows: 42,
    remainingRows: 0,
    complete: true,
  });
});

test("invalid pagination inputs fail closed", () => {
  assert.throws(() => resultTablePageState(-1, 0), /non-negative integer/);
  assert.throws(() => resultTablePageState(10, 1.5), /non-negative integer/);
  assert.throws(() => nextVisibleRowCount(10, 5, 0), /positive integer/);
});

test("static build publishes the result pagination module and stylesheet", async () => {
  const index = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const build = await readFile(new URL("../scripts/build.mjs", import.meta.url), "utf8");
  const styles = await readFile(new URL("../result-table.css", import.meta.url), "utf8");

  assert.match(index, /result-table\.css/);
  assert.match(index, /apps\/web\/src\/result-table\.js/);
  assert.match(build, /result-table\.css/);
  assert.match(build, /result table pagination/);
  assert.match(styles, /result-pagination/);
  assert.match(styles, /tbody tr\[hidden\]/);
});
