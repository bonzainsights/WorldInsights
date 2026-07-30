import assert from "node:assert/strict";
import test from "node:test";
import {
  decodeRecipeToken,
  encodeRecipeToken,
  recipeForSelection,
  recipeFromUrl,
  urlWithRecipe,
} from "../dist/apps/web/src/recipe-url.js";

const PYTHON_TOKEN = "eNpdj9FuwjAMRf_Fz2m0wtP6KxOqTOKVaEkc2aGIIf59LkybxItlX9nnXt9gIV4E2-kK0-1_mFNUmD5Gtz84KBwJJkg15LN1d2dtTAE7y7yiJKz9dx8uR6_NN26-c8_gNqFe_RJNDNh8iGBAbiTYE1ejqnE6ia0KZUIlQ5l8YclxOGL9Gv7MdNi9je9WdvtBsbRMdqXhRAXnlUQfwNFBT4W2b15yOzDbxM-gGwQO9koXrPrJUjbZsq1Jz5jT92u--w-O02aE";

const recipe = recipeForSelection(
  "world-bank-indicators-2019-2023-sample",
  "scatter",
  ["wb.sp.pop.totl", "wb.ny.gdp.pcap.cd"],
  { geography_ids: [3, 1], periods: ["2023"] },
);

test("browser recipe encoding round-trips through strict validation", async () => {
  const token = await encodeRecipeToken(recipe);
  assert.deepEqual(await decodeRecipeToken(token), recipe);
  assert.doesNotMatch(token, /[+/=]/);
});

test("decodes the Python zlib recipe token", async () => {
  assert.deepEqual(await decodeRecipeToken(PYTHON_TOKEN), recipe);
});

test("builds and restores exactly one URL recipe parameter", async () => {
  const url = await urlWithRecipe("https://example.test/explorer?keep=yes#result", recipe);
  const parsed = new URL(url);
  assert.equal(parsed.searchParams.get("keep"), "yes");
  assert.equal(parsed.hash, "#result");
  assert.deepEqual(await recipeFromUrl(url), recipe);
  parsed.searchParams.append("r", "duplicate");
  await assert.rejects(recipeFromUrl(parsed.toString()), /exactly one/);
});

test("fails closed for malformed or oversized recipe tokens", async () => {
  await assert.rejects(decodeRecipeToken("not_valid!"), /invalid recipe token/);
  await assert.rejects(decodeRecipeToken("a".repeat(32_769)), /too large/);
});

test("uses all-compatible scope when no explicit subset exists", () => {
  const all = recipeForSelection("release", "trend", ["population"], {});
  assert.deepEqual(all.geography, { mode: "all_compatible", geography_ids: [] });
  assert.deepEqual(all.time, { mode: "all_compatible", periods: [] });
  assert.equal(all.visualization, "line");
});
