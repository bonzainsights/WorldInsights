import {
  parseCoverageManifestV1,
  parseObservationsV1,
  parseReleaseManifestV1,
  type CoverageManifestV1,
  type LatestReleaseV1,
  type ObservationV1,
  type ReleaseManifestV1,
} from "../../../packages/contracts/src/index.js";
import {
  parseCatalogReleaseV2,
  parseLatestRelease,
  type CatalogIndicatorV2,
  type CatalogReleaseV2,
  type LatestReleaseV2,
} from "../../../packages/contracts/src/catalog-v2.js";

export interface StaticSingleIndicatorRelease {
  kind: "single";
  latest: LatestReleaseV1;
  manifest: ReleaseManifestV1;
  coverage: CoverageManifestV1;
  observations: ObservationV1[];
}

export interface StaticCatalogRelease {
  kind: "catalog";
  latest: LatestReleaseV2;
  catalog: CatalogReleaseV2;
  catalogUrl: URL;
}

export interface StaticCatalogIndicator {
  metadata: CatalogIndicatorV2;
  coverage: CoverageManifestV1;
  observations: ObservationV1[];
}

export type StaticRelease = StaticSingleIndicatorRelease | StaticCatalogRelease;
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
  const latest = parseLatestRelease(parseJson(latestText, latestUrl));

  if (latest.schema_version === 2) {
    const catalogUrl = safeAssetUrl(latest.catalog, normalizedBase);
    const catalogText = await fetchText(catalogUrl, fetcher);
    await assertSha256(catalogText, latest.catalog_sha256, "catalog");
    const catalog = parseCatalogReleaseV2(parseJson(catalogText, catalogUrl));
    if (catalog.release.release_id !== latest.release_id) {
      throw new ReleaseLoadError("latest release ID does not match the catalog");
    }
    return { kind: "catalog", latest, catalog, catalogUrl };
  }

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
    manifest.files,
    fetcher,
    parseCoverageManifestV1,
  );
  const observations = await loadChecksummedJson(
    "observations.json",
    releaseDirectory,
    manifest.files,
    fetcher,
    parseObservationsV1,
  );

  validateIndicatorConsistency(
    manifest.release.release_id,
    manifest.indicator.indicator_variant_id,
    manifest.row_count,
    coverage,
    observations,
  );
  return { kind: "single", latest, manifest, coverage, observations };
}

export async function loadCatalogCoverage(
  release: StaticCatalogRelease,
  indicatorVariantId: string,
  fetcher: FetchLike = globalThis.fetch.bind(globalThis),
): Promise<CoverageManifestV1> {
  const metadata = findCatalogIndicator(release, indicatorVariantId);
  const coverage = await loadChecksummedJson(
    metadata.coverage,
    new URL("./", release.catalogUrl),
    release.catalog.files,
    fetcher,
    parseCoverageManifestV1,
  );
  if (coverage.indicator_variant_id !== metadata.indicator_variant_id) {
    throw new ReleaseLoadError("coverage indicator does not match the catalog");
  }
  return coverage;
}

export async function loadCatalogObservations(
  release: StaticCatalogRelease,
  indicatorVariantId: string,
  fetcher: FetchLike = globalThis.fetch.bind(globalThis),
): Promise<ObservationV1[]> {
  const metadata = findCatalogIndicator(release, indicatorVariantId);
  const observations = await loadChecksummedJson(
    metadata.observations,
    new URL("./", release.catalogUrl),
    release.catalog.files,
    fetcher,
    parseObservationsV1,
  );
  if (observations.length !== metadata.row_count) {
    throw new ReleaseLoadError("declared row count does not match observations");
  }
  for (const observation of observations) {
    if (observation.release_id !== release.catalog.release.release_id) {
      throw new ReleaseLoadError("observation release ID does not match the release");
    }
    if (observation.indicator_variant_id !== metadata.indicator_variant_id) {
      throw new ReleaseLoadError("observation indicator does not match the catalog");
    }
  }
  return observations;
}

export async function loadCatalogIndicator(
  release: StaticCatalogRelease,
  indicatorVariantId: string,
  fetcher: FetchLike = globalThis.fetch.bind(globalThis),
): Promise<StaticCatalogIndicator> {
  const metadata = findCatalogIndicator(release, indicatorVariantId);
  const [coverage, observations] = await Promise.all([
    loadCatalogCoverage(release, indicatorVariantId, fetcher),
    loadCatalogObservations(release, indicatorVariantId, fetcher),
  ]);
  validateIndicatorConsistency(
    release.catalog.release.release_id,
    metadata.indicator_variant_id,
    metadata.row_count,
    coverage,
    observations,
  );
  return { metadata, coverage, observations };
}

function findCatalogIndicator(
  release: StaticCatalogRelease,
  indicatorVariantId: string,
): CatalogIndicatorV2 {
  const metadata = release.catalog.indicators.find(
    (indicator) => indicator.indicator_variant_id === indicatorVariantId,
  );
  if (!metadata) {
    throw new ReleaseLoadError(`catalog does not contain indicator: ${indicatorVariantId}`);
  }
  return metadata;
}

async function loadChecksummedJson<T>(
  path: string,
  releaseDirectory: URL,
  files: Record<string, { sha256: string }>,
  fetcher: FetchLike,
  parser: (value: unknown) => T,
): Promise<T> {
  const metadata = files[path];
  if (!metadata) throw new ReleaseLoadError(`release does not declare ${path}`);
  const url = safeAssetUrl(path, releaseDirectory);
  const text = await fetchText(url, fetcher);
  await assertSha256(text, metadata.sha256, path);
  return parser(parseJson(text, url));
}

function validateIndicatorConsistency(
  releaseId: string,
  indicatorVariantId: string,
  rowCount: number,
  coverage: CoverageManifestV1,
  observations: ObservationV1[],
): void {
  if (rowCount !== observations.length) {
    throw new ReleaseLoadError("declared row count does not match observations");
  }
  if (coverage.indicator_variant_id !== indicatorVariantId) {
    throw new ReleaseLoadError("coverage indicator does not match the catalog");
  }
  const geographyIds = new Set(coverage.geography_ids);
  const periods = new Set(coverage.periods);
  for (const observation of observations) {
    if (observation.release_id !== releaseId) {
      throw new ReleaseLoadError("observation release ID does not match the release");
    }
    if (observation.indicator_variant_id !== indicatorVariantId) {
      throw new ReleaseLoadError("observation indicator does not match the catalog");
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
