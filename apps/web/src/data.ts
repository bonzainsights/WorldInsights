import {
  parseCoverageManifestV1,
  parseLatestReleaseV1,
  parseObservationsV1,
  parseReleaseManifestV1,
  type CoverageManifestV1,
  type LatestReleaseV1,
  type ObservationV1,
  type ReleaseManifestV1,
} from "../../../packages/contracts/src/index.js";

export interface StaticRelease {
  latest: LatestReleaseV1;
  manifest: ReleaseManifestV1;
  coverage: CoverageManifestV1;
  observations: ObservationV1[];
}

export type FetchLike = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export class ReleaseLoadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ReleaseLoadError";
  }
}

export async function loadStaticRelease(
  baseUrl: string | URL = new URL("./data/", globalThis.location?.href ?? "http://localhost/"),
  fetcher: FetchLike = globalThis.fetch.bind(globalThis),
): Promise<StaticRelease> {
  const normalizedBase = directoryUrl(baseUrl);
  const latestUrl = new URL("latest.json", normalizedBase);
  const latestText = await fetchText(latestUrl, fetcher);
  const latest = parseLatestReleaseV1(parseJson(latestText, latestUrl));

  const manifestUrl = safeAssetUrl(latest.manifest, normalizedBase);
  const manifestText = await fetchText(manifestUrl, fetcher);
  await assertSha256(manifestText, latest.manifest_sha256, "manifest");
  const manifest = parseReleaseManifestV1(parseJson(manifestText, manifestUrl));
  if (manifest.release.release_id !== latest.release_id) {
    throw new ReleaseLoadError("latest release ID does not match the manifest");
  }

  const releaseDirectory = new URL("./", manifestUrl);
  const coverage = await loadChecksummedJson(
    "coverage.json",
    releaseDirectory,
    manifest,
    fetcher,
    parseCoverageManifestV1,
  );
  const observations = await loadChecksummedJson(
    "observations.json",
    releaseDirectory,
    manifest,
    fetcher,
    parseObservationsV1,
  );

  validateReleaseConsistency(manifest, coverage, observations);
  return { latest, manifest, coverage, observations };
}

async function loadChecksummedJson<T>(
  path: string,
  releaseDirectory: URL,
  manifest: ReleaseManifestV1,
  fetcher: FetchLike,
  parser: (value: unknown) => T,
): Promise<T> {
  const metadata = manifest.files[path];
  if (!metadata) throw new ReleaseLoadError(`manifest does not declare ${path}`);
  const url = safeAssetUrl(path, releaseDirectory);
  const text = await fetchText(url, fetcher);
  await assertSha256(text, metadata.sha256, path);
  return parser(parseJson(text, url));
}

function validateReleaseConsistency(
  manifest: ReleaseManifestV1,
  coverage: CoverageManifestV1,
  observations: ObservationV1[],
): void {
  if (manifest.row_count !== observations.length) {
    throw new ReleaseLoadError("manifest row count does not match observations");
  }
  if (coverage.indicator_variant_id !== manifest.indicator.indicator_variant_id) {
    throw new ReleaseLoadError("coverage indicator does not match the manifest");
  }
  const geographyIds = new Set(coverage.geography_ids);
  const periods = new Set(coverage.periods);
  for (const observation of observations) {
    if (observation.release_id !== manifest.release.release_id) {
      throw new ReleaseLoadError("observation release ID does not match the manifest");
    }
    if (observation.indicator_variant_id !== manifest.indicator.indicator_variant_id) {
      throw new ReleaseLoadError("observation indicator does not match the manifest");
    }
    if (!geographyIds.has(observation.geography_id)) {
      throw new ReleaseLoadError("observation geography is absent from coverage");
    }
    if (!periods.has(observation.period_label)) {
      throw new ReleaseLoadError("observation period is absent from coverage");
    }
  }
}

async function fetchText(url: URL, fetcher: FetchLike): Promise<string> {
  let response: Response;
  try {
    response = await fetcher(url);
  } catch (error) {
    throw new ReleaseLoadError(`failed to fetch ${url.pathname}: ${errorMessage(error)}`);
  }
  if (!response.ok) {
    throw new ReleaseLoadError(`failed to fetch ${url.pathname}: HTTP ${response.status}`);
  }
  return response.text();
}

function parseJson(text: string, url: URL): unknown {
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new ReleaseLoadError(`invalid JSON at ${url.pathname}: ${errorMessage(error)}`);
  }
}

async function assertSha256(text: string, expected: string, label: string): Promise<void> {
  const actual = await sha256Hex(new TextEncoder().encode(text));
  if (actual !== expected) {
    throw new ReleaseLoadError(`${label} checksum mismatch`);
  }
}

async function sha256Hex(content: Uint8Array): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest("SHA-256", content);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function safeAssetUrl(path: string, base: URL): URL {
  const url = new URL(path, base);
  if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) {
    throw new ReleaseLoadError(`asset path escapes its release directory: ${path}`);
  }
  return url;
}

function directoryUrl(value: string | URL): URL {
  const url = value instanceof URL ? new URL(value) : new URL(value, "http://localhost/");
  if (!url.pathname.endsWith("/")) url.pathname += "/";
  return url;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
