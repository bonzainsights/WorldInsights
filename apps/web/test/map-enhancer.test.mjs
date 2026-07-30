import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("the static shell loads the map enhancer after the primary explorer", async () => {
  const index = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const mainPosition = index.indexOf("main.js");
  const enhancerPosition = index.indexOf("map-enhancer.js");
  assert.ok(mainPosition >= 0);
  assert.ok(enhancerPosition > mainPosition);
});

test("the enhancer waits for verified table results and removes duplicate export controls", async () => {
  const source = await readFile(new URL("../dist/apps/web/src/map-enhancer.js", import.meta.url), "utf8");
  assert.match(source, /operation\.value !== "map"/);
  assert.match(source, /querySelector\("\.data-table"\)/);
  assert.match(source, /deduplicateExportButtons/);
  assert.match(source, /buttons\.slice\(0, -1\)/);
  assert.match(source, /loadCompatibleObservations/);
  assert.match(source, /loadWorldTopology/);
  assert.match(source, /MutationObserver/);
});
