import {
  ContractError,
  parseLatestReleaseV1,
  type Frequency,
  type GeographyType,
  type LatestReleaseV1,
} from "./index.js";

export interface LatestReleaseV2 {
  schema_version: 2;
  release_id: string;
  catalog: string;
  catalog_sha256: string;
}


export interface CatalogGeographyV2 {
  geography_id: number;
  canonical_code: string;
  name: string;
  geography_type: GeographyType;
  parent_id: number | null;
  valid_from: string | null;
  valid_to: string | null;
}

export interface CatalogIndicatorV2 {
  indicator_variant_id: string;
  provider_id: string;
  dataset_id: string;
  provider_indicator_code: string;
  name: string;
  concept_id: string;
  unit_id: string;
  frequency: Frequency;
  geography_types: GeographyType[];
  row_count: number;
  observations: string;
  coverage: string;
}

export interface CatalogReleaseV2 {
  schema_version: 2;
  release: {
    release_id: string;
    provider_id: string;
    dataset_id: string;
    retrieved_at: string;
    source_checksum: string;
    pipeline_version: string;
  };
  geographies: CatalogGeographyV2[];
  indicators: CatalogIndicatorV2[];
  files: Record<string, { sha256: string }>;
}

export type LatestRelease = LatestReleaseV1 | LatestReleaseV2;

const GEOGRAPHY_TYPES = new Set<GeographyType>([
  "country",
  "territory",
  "region",
  "aggregate",
]);
const FREQUENCIES = new Set<Frequency>(["annual", "quarterly", "monthly", "irregular"]);

export function parseLatestRelease(value: unknown): LatestRelease {
  const root = object(value, "latest");
  return root.schema_version === 2
    ? parseLatestReleaseV2(value)
    : parseLatestReleaseV1(value);
}

export function parseLatestReleaseV2(value: unknown): LatestReleaseV2 {
  const root = object(value, "latest");
  exactKeys(root, ["schema_version", "release_id", "catalog", "catalog_sha256"], "latest");
  literal(root.schema_version, 2, "latest.schema_version");
  return {
    schema_version: 2,
    release_id: nonEmptyString(root.release_id, "latest.release_id"),
    catalog: safeRelativeAssetPath(root.catalog, "latest.catalog"),
    catalog_sha256: sha256(root.catalog_sha256, "latest.catalog_sha256"),
  };
}

export function parseCatalogReleaseV2(value: unknown): CatalogReleaseV2 {
  const root = object(value, "catalog");
  exactKeys(root, ["schema_version", "release", "geographies", "indicators", "files"], "catalog");
  literal(root.schema_version, 2, "catalog.schema_version");

  const release = object(root.release, "catalog.release");
  exactKeys(release, [
    "release_id",
    "provider_id",
    "dataset_id",
    "retrieved_at",
    "source_checksum",
    "pipeline_version",
  ], "catalog.release");
  const parsedRelease = {
    release_id: nonEmptyString(release.release_id, "catalog.release.release_id"),
    provider_id: nonEmptyString(release.provider_id, "catalog.release.provider_id"),
    dataset_id: nonEmptyString(release.dataset_id, "catalog.release.dataset_id"),
    retrieved_at: isoDateTime(release.retrieved_at, "catalog.release.retrieved_at"),
    source_checksum: sha256(release.source_checksum, "catalog.release.source_checksum"),
    pipeline_version: nonEmptyString(release.pipeline_version, "catalog.release.pipeline_version"),
  };

  const geographies = array(root.geographies, "catalog.geographies").map((item, index) => {
    const geography = object(item, `catalog.geographies[${index}]`);
    exactKeys(geography, [
      "geography_id",
      "canonical_code",
      "name",
      "geography_type",
      "parent_id",
      "valid_from",
      "valid_to",
    ], `catalog.geographies[${index}]`);
    const validFrom = nullableIsoDate(
      geography.valid_from,
      `catalog.geographies[${index}].valid_from`,
    );
    const validTo = nullableIsoDate(
      geography.valid_to,
      `catalog.geographies[${index}].valid_to`,
    );
    if (validFrom !== null && validTo !== null && validFrom > validTo) {
      fail(`catalog.geographies[${index}] valid_from is after valid_to`);
    }
    return {
      geography_id: positiveInteger(
        geography.geography_id,
        `catalog.geographies[${index}].geography_id`,
      ),
      canonical_code: nonEmptyString(
        geography.canonical_code,
        `catalog.geographies[${index}].canonical_code`,
      ),
      name: nonEmptyString(geography.name, `catalog.geographies[${index}].name`),
      geography_type: enumValue(
        geography.geography_type,
        GEOGRAPHY_TYPES,
        `catalog.geographies[${index}].geography_type`,
      ),
      parent_id: nullablePositiveInteger(
        geography.parent_id,
        `catalog.geographies[${index}].parent_id`,
      ),
      valid_from: validFrom,
      valid_to: validTo,
    } satisfies CatalogGeographyV2;
  });
  if (geographies.length === 0) fail("catalog must contain at least one geography");
  unique(geographies.map((item) => item.geography_id), "catalog geography IDs");
  unique(geographies.map((item) => item.canonical_code), "catalog geography codes");
  const knownGeographyIds = new Set(geographies.map((item) => item.geography_id));
  for (const [index, geography] of geographies.entries()) {
    if (geography.parent_id !== null && !knownGeographyIds.has(geography.parent_id)) {
      fail(`catalog.geographies[${index}] parent is not declared`);
    }
  }

  const fileObject = object(root.files, "catalog.files");
  const files: Record<string, { sha256: string }> = {};
  for (const [path, metadataValue] of Object.entries(fileObject)) {
    const safePath = safeRelativeAssetPath(path, "catalog file path");
    const metadata = object(metadataValue, `catalog.files.${path}`);
    exactKeys(metadata, ["sha256"], `catalog.files.${path}`);
    files[safePath] = { sha256: sha256(metadata.sha256, `catalog.files.${path}.sha256`) };
  }

  const indicators = array(root.indicators, "catalog.indicators").map((item, index) => {
    const indicator = object(item, `catalog.indicators[${index}]`);
    exactKeys(indicator, [
      "indicator_variant_id",
      "provider_id",
      "dataset_id",
      "provider_indicator_code",
      "name",
      "concept_id",
      "unit_id",
      "frequency",
      "geography_types",
      "row_count",
      "observations",
      "coverage",
    ], `catalog.indicators[${index}]`);
    const parsed: CatalogIndicatorV2 = {
      indicator_variant_id: nonEmptyString(
        indicator.indicator_variant_id,
        `catalog.indicators[${index}].indicator_variant_id`,
      ),
      provider_id: nonEmptyString(indicator.provider_id, `catalog.indicators[${index}].provider_id`),
      dataset_id: nonEmptyString(indicator.dataset_id, `catalog.indicators[${index}].dataset_id`),
      provider_indicator_code: nonEmptyString(
        indicator.provider_indicator_code,
        `catalog.indicators[${index}].provider_indicator_code`,
      ),
      name: nonEmptyString(indicator.name, `catalog.indicators[${index}].name`),
      concept_id: nonEmptyString(indicator.concept_id, `catalog.indicators[${index}].concept_id`),
      unit_id: nonEmptyString(indicator.unit_id, `catalog.indicators[${index}].unit_id`),
      frequency: enumValue(indicator.frequency, FREQUENCIES, `catalog.indicators[${index}].frequency`),
      geography_types: array(
        indicator.geography_types,
        `catalog.indicators[${index}].geography_types`,
      ).map((entry, geographyIndex) =>
        enumValue(
          entry,
          GEOGRAPHY_TYPES,
          `catalog.indicators[${index}].geography_types[${geographyIndex}]`,
        ),
      ),
      row_count: nonNegativeInteger(indicator.row_count, `catalog.indicators[${index}].row_count`),
      observations: safeRelativeAssetPath(
        indicator.observations,
        `catalog.indicators[${index}].observations`,
      ),
      coverage: safeRelativeAssetPath(
        indicator.coverage,
        `catalog.indicators[${index}].coverage`,
      ),
    };
    if (parsed.provider_id !== parsedRelease.provider_id) {
      fail(`catalog.indicators[${index}] provider does not match release`);
    }
    if (parsed.dataset_id !== parsedRelease.dataset_id) {
      fail(`catalog.indicators[${index}] dataset does not match release`);
    }
    if (!files[parsed.observations] || !files[parsed.coverage]) {
      fail(`catalog.indicators[${index}] references an undeclared file`);
    }
    return parsed;
  });
  if (indicators.length === 0) fail("catalog must contain at least one indicator");
  unique(indicators.map((indicator) => indicator.indicator_variant_id), "catalog indicator IDs");

  return { schema_version: 2, release: parsedRelease, geographies, indicators, files };
}

function object(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    fail(`${field} must be an object`);
  }
  return value as Record<string, unknown>;
}

function array(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) fail(`${field} must be an array`);
  return value;
}

function nonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) fail(`${field} must be a non-empty string`);
  return value;
}

function positiveInteger(value: unknown, field: string): number {
  if (!Number.isInteger(value) || (value as number) <= 0) {
    fail(`${field} must be a positive integer`);
  }
  return value as number;
}

function nullablePositiveInteger(value: unknown, field: string): number | null {
  return value === null ? null : positiveInteger(value, field);
}

function nonNegativeInteger(value: unknown, field: string): number {
  if (!Number.isInteger(value) || (value as number) < 0) {
    fail(`${field} must be a non-negative integer`);
  }
  return value as number;
}

function enumValue<T extends string>(value: unknown, allowed: Set<T>, field: string): T {
  if (typeof value !== "string" || !allowed.has(value as T)) fail(`${field} is unsupported`);
  return value as T;
}

function literal<T extends number>(value: unknown, expected: T, field: string): T {
  if (value !== expected) fail(`${field} must equal ${String(expected)}`);
  return expected;
}

function exactKeys(value: Record<string, unknown>, expected: string[], field: string): void {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    fail(`${field} has invalid fields`);
  }
}

function unique<T>(values: T[], field: string): void {
  if (new Set(values).size !== values.length) fail(`${field} must contain unique values`);
}

function safeRelativeAssetPath(value: unknown, field: string): string {
  const text = nonEmptyString(value, field);
  if (
    text.startsWith("/") ||
    text.includes("\\") ||
    text.split("/").some((part) => !part || part === "." || part === "..")
  ) {
    fail(`${field} must be a safe relative asset path`);
  }
  return text;
}

function sha256(value: unknown, field: string): string {
  const text = nonEmptyString(value, field);
  if (!/^[a-f0-9]{64}$/.test(text)) {
    fail(`${field} must be a lowercase SHA-256 hex digest`);
  }
  return text;
}

function nullableIsoDate(value: unknown, field: string): string | null {
  if (value === null) return null;
  const text = nonEmptyString(value, field);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text) || Number.isNaN(Date.parse(`${text}T00:00:00Z`))) {
    fail(`${field} must be an ISO date or null`);
  }
  return text;
}

function isoDateTime(value: unknown, field: string): string {
  const text = nonEmptyString(value, field);
  if (!/(Z|[+-]\d{2}:\d{2})$/.test(text) || Number.isNaN(Date.parse(text))) {
    fail(`${field} must be a timezone-aware ISO datetime`);
  }
  return text;
}

function fail(message: string): never {
  throw new ContractError(message);
}
