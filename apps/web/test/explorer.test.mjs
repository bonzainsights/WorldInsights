import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { CatalogExplorer } from "../dist/apps/web/src/explorer.js";
import { ReleaseLoadError, loadStaticRelease } from "../dist/apps/web/src/data.js";

async function fixtureFiles() {
  const root = new URL(
    "../../../tests/fixtures/contracts/catalog-release-v2/",
    import.meta.url,
  );
  const latest = JSON.parse(await readFile(new URL("latest.json", root), "utf8"));
  const catalog = JSON.parse(await readFile(new URL(latest.catalog, root), "utf8"));
  const paths = ["latest.json", latest.catalog, ...Object.keys(catalog.files)];
  const prefix = `releases/${latest.release_id}/`;
  return new Map(
    await Promise.all(
      paths.map(async (path) => {
        const fixturePath = path === "latest.json" || path === latest.catalog
          ? path
          : `${prefix}${path}`;
        return [`/data/${fixturePath}`, await readFile(new URL(fixturePath, root), "utf8")];
      }),
    ),
  );
}

function trackedFetch(files, requests) {
  return async (input) => {
    const url = new URL(input);
    requests.push(url.pathname);
    const body = files.get(url.pathname);
    return body === undefined ? new Response("not found", { status: 404 }) : new Response(body);
  };
}

test("rejects invalid arity without fetching coverage", async () => {
  const files = await fixtureFiles();
  const requests = [];
  const fetcher = trackedFetch(files, requests);
  const release = await loadStaticRelease("https://example.test/data/", fetcher);
  const explorer = new CatalogExplorer(release, fetcher);
  explorer.setSelection("scatter", ["wb.sp.pop.totl"]);

  const result = await explorer.evaluate();
  assert.deepEqual(result.blockers, ["operation_arity"]);
  assert.equal(requests.length, 2);
});

test("evaluates coverage before lazily loading compatible observations", async () => {
  const files = await fixtureFiles();
  const requests = [];
  const fetcher = trackedFetch(files, requests);
  const release = await loadStaticRelease("https://example.test/data/", fetcher);
  const explorer = new CatalogExplorer(release, fetcher);
  explorer.setSelection("scatter", ["wb.sp.pop.totl", "test.gdp.per.capita"]);

  const compatibility = await explorer.evaluate();
  assert.deepEqual(compatibility.geography_ids, [2]);
  assert.equal(requests.filter((path) => path.endsWith("coverage.json")).length, 2);
  assert.equal(requests.filter((path) => path.endsWith("observations.json")).length, 0);

  const result = await explorer.loadCompatibleObservations();
  assert.deepEqual(
    [...result.observations.values()].map((rows) => rows.map((row) => row.geography_id)),
    [[2], [2]],
  );
  assert.equal(requests.filter((path) => path.endsWith("observations.json")).length, 2);

  await explorer.loadCompatibleObservations();
  assert.equal(requests.filter((path) => path.endsWith("coverage.json")).length, 2);
  assert.equal(requests.filter((path) => path.endsWith("observations.json")).length, 2);
});

test("does not load observations for an invalid ratio", async () => {
  const files = await fixtureFiles();
  const requests = [];
  const fetcher = trackedFetch(files, requests);
  const release = await loadStaticRelease("https://example.test/data/", fetcher);
  const explorer = new CatalogExplorer(release, fetcher);
  explorer.setSelection("ratio", ["wb.sp.pop.totl", "test.gdp.per.capita"]);

  await assert.rejects(
    explorer.loadCompatibleObservations(),
    (error) => error instanceof ReleaseLoadError && /unit_mismatch/.test(error.message),
  );
  assert.equal(requests.filter((path) => path.endsWith("observations.json")).length, 0);
});
