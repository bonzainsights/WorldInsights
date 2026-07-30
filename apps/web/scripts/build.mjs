import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDirectory, "..");
const repositoryRoot = resolve(appRoot, "../..");
const output = resolve(appRoot, "dist");

await rm(output, { recursive: true, force: true });
const result = spawnSync("tsc", ["-p", "tsconfig.json"], {
  cwd: appRoot,
  stdio: "inherit",
});
if (result.status !== 0) process.exit(result.status ?? 1);

await mkdir(output, { recursive: true });
await cp(resolve(appRoot, "index.html"), resolve(output, "index.html"));
await cp(resolve(appRoot, "styles.css"), resolve(output, "styles.css"));
const sampleResult = spawnSync(
  "python",
  [resolve(repositoryRoot, "scripts/build_sample_release.py"), "--output", resolve(output, "data")],
  {
    cwd: repositoryRoot,
    stdio: "inherit",
    env: { ...process.env, PYTHONPATH: resolve(repositoryRoot, "pipeline") },
  },
);
if (sampleResult.status !== 0) process.exit(sampleResult.status ?? 1);

const buildMetadata = {
  built_at: new Date().toISOString(),
  data_source: "pinned World Bank population and GDP-per-capita fixtures",
  release_schema: 2,
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
