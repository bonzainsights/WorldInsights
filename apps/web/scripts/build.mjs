import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDirectory, "..");
const repositoryRoot = resolve(appRoot, "../..");
const output = resolve(appRoot, "dist");
const releaseMode = process.env.WORLDINSIGHTS_RELEASE_MODE ?? "sample";
const releaseScope = process.env.WORLDINSIGHTS_RELEASE_SCOPE ?? "bounded";

if (!new Set(["sample", "live"]).has(releaseMode)) {
  throw new Error(`unsupported WORLDINSIGHTS_RELEASE_MODE: ${releaseMode}`);
}
if (!new Set(["bounded", "global"]).has(releaseScope)) {
  throw new Error(`unsupported WORLDINSIGHTS_RELEASE_SCOPE: ${releaseScope}`);
}

await rm(output, { recursive: true, force: true });
const result = spawnSync("tsc", ["-p", "tsconfig.json"], {
  cwd: appRoot,
  stdio: "inherit",
});
if (result.status !== 0) process.exit(result.status ?? 1);

await mkdir(output, { recursive: true });
await cp(resolve(appRoot, "index.html"), resolve(output, "index.html"));
await cp(resolve(appRoot, "styles.css"), resolve(output, "styles.css"));
await cp(resolve(appRoot, "country-scope.css"), resolve(output, "country-scope.css"));
await cp(resolve(appRoot, "result-table.css"), resolve(output, "result-table.css"));
await cp(resolve(appRoot, "scope-policy.css"), resolve(output, "scope-policy.css"));

const releaseArguments = releaseMode === "live"
  ? liveReleaseArguments()
  : [
      resolve(repositoryRoot, "scripts/build_sample_release.py"),
      "--output",
      resolve(output, "data"),
    ];
const releaseResult = spawnSync("python", releaseArguments, {
  cwd: repositoryRoot,
  stdio: "inherit",
  env: { ...process.env, PYTHONPATH: resolve(repositoryRoot, "pipeline") },
});
if (releaseResult.status !== 0) process.exit(releaseResult.status ?? 1);

const buildMetadata = {
  built_at: new Date().toISOString(),
  release_mode: releaseMode,
  data_source: releaseMode === "live"
    ? releaseScope === "global"
      ? "live global World Bank Indicators API"
      : "live bounded World Bank Indicators API"
    : "pinned World Bank population and GDP-per-capita fixtures",
  release_schema: 2,
  ...(releaseMode === "live"
    ? {
        release_scope: releaseScope,
        start_year: parseYear("WORLDINSIGHTS_START_YEAR", "2019"),
        end_year: parseYear("WORLDINSIGHTS_END_YEAR", "2024"),
      }
    : {}),
};
await writeFile(
  resolve(output, "build.json"),
  `${JSON.stringify(buildMetadata, null, 2)}\n`,
  "utf8",
);

const index = await readFile(resolve(output, "index.html"), "utf8");
if (!index.includes("apps/web/src/main.js")) {
  throw new Error("index.html does not reference the compiled application entry point");
}
if (!index.includes("apps/web/src/country-scope.js")) {
  throw new Error("index.html does not reference the country scope enhancement");
}
if (!index.includes("apps/web/src/result-table.js")) {
  throw new Error("index.html does not reference result table pagination");
}
if (!index.includes("apps/web/src/scope-policy-ui.js")) {
  throw new Error("index.html does not reference chart scope policy guidance");
}

function liveReleaseArguments() {
  const startYear = parseYear("WORLDINSIGHTS_START_YEAR", "2019");
  const endYear = parseYear("WORLDINSIGHTS_END_YEAR", "2024");
  if (startYear > endYear) {
    throw new Error("WORLDINSIGHTS_START_YEAR cannot be after WORLDINSIGHTS_END_YEAR");
  }
  const script = releaseScope === "global"
    ? "build_global_world_bank_release.py"
    : "build_live_world_bank_release.py";
  return [
    resolve(repositoryRoot, "scripts", script),
    "--output",
    resolve(output, "data"),
    "--start-year",
    String(startYear),
    "--end-year",
    String(endYear),
  ];
}

function parseYear(name, fallback) {
  const value = process.env[name] ?? fallback;
  if (!/^\d{4}$/.test(value)) {
    throw new Error(`${name} must be a four-digit year`);
  }
  return Number(value);
}
