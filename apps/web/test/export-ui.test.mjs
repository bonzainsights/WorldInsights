import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("loaded results create and wire the CSV download control", async () => {
  const main = await readFile(new URL("../dist/apps/web/src/main.js", import.meta.url), "utf8");
  assert.match(main, /Download CSV/);
  assert.match(main, /compatibleObservationsCsv/);
  assert.match(main, /downloadCsv/);
  assert.match(main, /results\.append\(exportButton\)/);
});
