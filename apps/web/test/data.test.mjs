import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { ReleaseLoadError, loadStaticRelease } from "../dist/apps/web/src/data.js";

const fixtureRoot = new URL("../../../tests/fixtures/contracts/static-release-v1/", import.meta.url);

async function fixtureFiles() {
  const latest = JSON.parse(await readFile(new URL("latest.json", fixtureRoot), "utf8"));
  const paths = [
    "latest.json",
    latest.manifest,
    `releases/${latest.release_id}/coverage.json`,
    `releases/${latest.release_id}/observations.json`,
  ];
  return new Map(
    await Promise.all(
      paths.map(async (path) => [
        `/data/${path}`,
        await readFile(new URL(path === "latest.json" ? path : path, fixtureRoot), "utf8"),
      ]),
    ),
  );
}

function mappedFetch(files) {
  return async (input) => {
    const url = new URL(input);
    const body = files.get(url.pathname);
    return body === undefined
      ? new Response("not found", { status: 404 })
      : new Response(body, { status: 200, headers: { "content-type": "application/json" } });
  };
}

test("loads and verifies a complete static release", async () => {
  const files = await fixtureFiles();
  const release = await loadStaticRelease("https://example.test/data/", mappedFetch(files));

  assert.equal(release.manifest.row_count, 3);
  assert.deepEqual(release.coverage.geography_ids, [1, 2, 3]);
  assert.equal(release.observations[1].provider_quality_flags[0], "E");
});

test("rejects a tampered observations asset", async () => {
  const files = await fixtureFiles();
  const path = "/data/releases/world-bank-population-2023-sample/observations.json";
  files.set(path, files.get(path).replace("83280000.0", "83280001.0"));

  await assert.rejects(
    loadStaticRelease("https://example.test/data/", mappedFetch(files)),
    (error) => error instanceof ReleaseLoadError && /checksum mismatch/.test(error.message),
  );
});

test("rejects release asset paths that escape the data directory", async () => {
  const files = await fixtureFiles();
  const latest = JSON.parse(files.get("/data/latest.json"));
  latest.manifest = "../outside.json";
  files.set("/data/latest.json", `${JSON.stringify(latest)}\n`);

  await assert.rejects(
    loadStaticRelease("https://example.test/data/", mappedFetch(files)),
    (error) => error instanceof ReleaseLoadError && /escapes/.test(error.message),
  );
});
