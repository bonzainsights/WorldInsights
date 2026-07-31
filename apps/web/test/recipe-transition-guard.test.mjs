import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  isTransientRecipeArityError,
  selectionHasValidOperationArity,
} from "../dist/apps/web/src/recipe-transition-guard.js";

test("recipe transitions require operation-compatible indicator counts", () => {
  assert.equal(selectionHasValidOperationArity("map", 1), true);
  assert.equal(selectionHasValidOperationArity("scatter", 2), true);
  assert.equal(selectionHasValidOperationArity("correlation", 2), true);
  assert.equal(selectionHasValidOperationArity("scatter", 1), false);
  assert.equal(selectionHasValidOperationArity("trend", 2), true);
  assert.throws(
    () => selectionHasValidOperationArity("map", -1),
    /non-negative integer/,
  );
});

test("only operation-arity contract rejections are transient", () => {
  assert.equal(
    isTransientRecipeArityError(new Error("operation scatter has invalid indicator arity")),
    true,
  );
  assert.equal(
    isTransientRecipeArityError(new Error("operation scatter has invalid visualization")),
    false,
  );
  assert.equal(isTransientRecipeArityError("operation scatter has invalid indicator arity"), false);
});

test("transition guard loads before the explorer entry point", async () => {
  const index = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const guard = index.indexOf("apps/web/src/recipe-transition-guard.js");
  const main = index.indexOf("apps/web/src/main.js");

  assert.ok(guard >= 0);
  assert.ok(main >= 0);
  assert.ok(guard < main);
});
