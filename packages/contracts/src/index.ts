export type Operation = "map" | "trend" | "table" | "scatter" | "ratio" | "correlation";
export type Visualization = "map" | "line" | "table" | "scatter" | "bar";
export type GeographySelectionMode = "all_compatible" | "include";
export type TimeSelectionMode = "latest" | "all_compatible" | "include";
export type JsonScalar = string | number | boolean | null;
export type GeographyType = "country" | "territory" | "region" | "aggregate";
export type Frequency = "annual" | "quarterly" | "monthly" | "irregular";
export type ObservationStatus =
  | "observed"
  | "estimated"
  | "modeled"
  | "provisional"
  | "revised"
  | "suppressed"
  | "missing"
  | "not_applicable";

export interface TransformSelectionV1 {
  transform_id: string;
  parameters: Record<string, JsonScalar>;
}

export interface ExplorationRecipeV1 {
  schema_version: 1;
  release_id: string;
  operation: Operation;
  indicator_variant_ids: string[];
  visualization: Visualization;
  geography: {
    mode: GeographySelectionMode;
    geography_ids: number[];
  };
  time: {
    mode: TimeSelectionMode;
    periods: string[];
  };
  transforms: TransformSelectionV1[];
}

export interface LatestReleaseV1 {
  schema_version: 1;
  release_id: string;
  manifest: string;
  manifest_sha256: string;
}

export interface ReleaseManifestV1 {
  schema_version: 1;
  release: {
    release_id: string;
    provider_id: string;
    dataset_id: string;
    retrieved_at: string;
    source_checksum: string;
    pipeline_version: string;
  };
  indicator: {
    indicator_variant_id: string;
    provider_id: string;
    dataset_id: string;
    provider_indicator_code: string;
    name: string;
    concept_id: string;
    unit_id: string;
    frequency: Frequency;
    geography_types: GeographyType[];
  };
  row_count: number;
  files: Record<string, { sha256: string }>;
}

export interface CoverageManifestV1 {
  indicator_variant_id: string;
  geography_bits_hex: string;
  geography_ids: number[];
  periods: string[];
  geography_types: GeographyType[];
  frequency: Frequency;
  concept_id: string;
  unit_id: string;
}

export interface ObservationV1 {
  release_id: string;
  indicator_variant_id: string;
  geography_id: number;
  period_start: string;
  period_end: string;
  period_label: string;
  frequency: Frequency;
  unit_id: string;
  status: ObservationStatus;
  value: number | null;
  provider_quality_flags: string[];
  system_quality_flags: string[];
}

const OPERATIONS = new Set<Operation>([
  "map",
  "trend",
  "table",
  "scatter",
  "ratio",
  "correlation",
]);
const VISUALIZATIONS = new Set<Visualization>(["map", "line", "table", "scatter", "bar"]);
const GEOGRAPHY_SELECTION_MODES = new Set<GeographySelectionMode>([
  "all_compatible",
  "include",
]);
const TIME_SELECTION_MODES = new Set<TimeSelectionMode>([
  "latest",
  "all_compatible",
  "include",
]);
const GEOGRAPHY_TYPES = new Set<GeographyType>([
  "country",
  "territory",
  "region",
  "aggregate",
]);
const FREQUENCIES = new Set<Frequency>(["annual", "quarterly", "monthly", "irregular"]);
const OBSERVATION_STATUSES = new Set<ObservationStatus>([
  "observed",
  "estimated",
  "modeled",
  "provisional",
  "revised",
  "suppressed",
  "missing",
  "not_applicable",
]);

const OPERATION_ARITY: Record<Operation, readonly [number, number | null]> = {
  map: [1, 1],
  trend: [1, null],
  table: [1, null],
  scatter: [2, 2],
  ratio: [2, 2],
  correlation: [2, null],
};
const ALLOWED_VISUALIZATIONS: Record<Operation, ReadonlySet<Visualization>> = {
  map: new Set(["map", "table"]),
  trend: new Set(["line", "table"]),
  table: new Set(["table"]),
  scatter: new Set(["scatter", "table"]),
  ratio: new Set(["line", "bar", "table"]),
  correlation: new Set(["scatter", "table"]),
};

export class ContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ContractError";
  }
}

export function parseExplorationRecipeV1(value: unknown): ExplorationRecipeV1 {
  const root = object(value, "recipe");
  exactKeys(root, [
    "schema_version",
    "release_id",
    "operation",
    "indicator_variant_ids",
    "visualization",
    "geography",
    "time",
    "transforms",
  ], "recipe");
  literal(root.schema_version, 1, "schema_version");

  const geography = object(root.geography, "geography");
  exactKeys(geography, ["mode", "geography_ids"], "geography");
  const geographyMode = enumValue(
    geography.mode,
    GEOGRAPHY_SELECTION_MODES,
    "geography.mode",
  );
  const geographyIds = array(geography.geography_ids, "geography.geography_ids").map(
    (item, index) => positiveInteger(item, `geography.geography_ids[${index}]`),
  );
  unique(geographyIds, "geography.geography_ids");
  if (geographyMode === "include" && geographyIds.length === 0) {
    fail("include geography selection requires at least one ID");
  }
  if (geographyMode === "all_compatible" && geographyIds.length !== 0) {
    fail("all-compatible geography selection cannot contain IDs");
  }

  const time = object(root.time, "time");
  exactKeys(time, ["mode", "periods"], "time");
  const timeMode = enumValue(time.mode, TIME_SELECTION_MODES, "time.mode");
  const periods = array(time.periods, "time.periods").map((item, index) =>
    nonEmptyString(item, `time.periods[${index}]`),
  );
  unique(periods, "time.periods");
  if (timeMode === "include" && periods.length === 0) {
    fail("include time selection requires at least one period");
  }
  if (timeMode !== "include" && periods.length !== 0) {
    fail("latest and all-compatible time selections cannot contain periods");
  }

  const transforms = array(root.transforms, "transforms").map((item, index) => {
    const transform = object(item, `transforms[${index}]`);
    exactKeys(transform, ["transform_id", "parameters"], `transforms[${index}]`);
    const parametersObject = object(transform.parameters, `transforms[${index}].parameters`);
    const parameters: Record<string, JsonScalar> = {};
    for (const [name, parameter] of Object.entries(parametersObject)) {
      if (!name.trim()) fail("transform parameter names cannot be empty");
      parameters[name] = jsonScalar(parameter, `transforms[${index}].parameters.${name}`);
    }
    return {
      transform_id: nonEmptyString(transform.transform_id, `transforms[${index}].transform_id`),
      parameters,
    };
  });

  const indicatorVariantIds = array(
    root.indicator_variant_ids,
    "indicator_variant_ids",
  ).map((item, index) => nonEmptyString(item, `indicator_variant_ids[${index}]`));
  unique(indicatorVariantIds, "indicator_variant_ids");
  const operation = enumValue(root.operation, OPERATIONS, "operation");
  const visualization = enumValue(root.visualization, VISUALIZATIONS, "visualization");
  const [minimum, maximum] = OPERATION_ARITY[operation];
  if (
    indicatorVariantIds.length < minimum ||
    (maximum !== null && indicatorVariantIds.length > maximum)
  ) {
    fail(`operation ${operation} has invalid indicator arity`);
  }
  if (!ALLOWED_VISUALIZATIONS[operation].has(visualization)) {
    fail(`visualization ${visualization} is not valid for operation ${operation}`);
  }

  return {
    schema_version: 1,
    release_id: nonEmptyString(root.release_id, "release_id"),
    operation,
    indicator_variant_ids: indicatorVariantIds,
    visualization,
    geography: { mode: geographyMode, geography_ids: geographyIds },
    time: { mode: timeMode, periods },
    transforms,
  };
}

export function parseLatestReleaseV1(value: unknown): LatestReleaseV1 {
  const root = object(value, "latest");
  exactKeys(root, ["schema_version", "release_id", "manifest", "manifest_sha256"], "latest");
  literal(root.schema_version, 1, "latest.schema_version");
  return {
    schema_version: 1,
    release_id: nonEmptyString(root.release_id, "latest.release_id"),
    manifest: nonEmptyString(root.manifest, "latest.manifest"),
    manifest_sha256: sha256(root.manifest_sha256, "latest.manifest_sha256"),
  };
}

export function parseReleaseManifestV1(value: unknown): ReleaseManifestV1 {
  const root = object(value, "manifest");
  exactKeys(root, ["schema_version", "release", "indicator", "row_count", "files"], "manifest");
  literal(root.schema_version, 1, "manifest.schema_version");

  const release = object(root.release, "manifest.release");
  exactKeys(release, [
    "release_id",
    "provider_id",
    "dataset_id",
    "retrieved_at",
    "source_checksum",
    "pipeline_version",
  ], "manifest.release");

  const indicator = object(root.indicator, "manifest.indicator");
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
  ], "manifest.indicator");

  const fileObject = object(root.files, "manifest.files");
  const files: Record<string, { sha256: string }> = {};
  for (const [path, metadataValue] of Object.entries(fileObject)) {
    if (!path.trim()) fail("manifest file path cannot be empty");
    const metadata = object(metadataValue, `manifest.files.${path}`);
    exactKeys(metadata, ["sha256"], `manifest.files.${path}`);
    files[path] = { sha256: sha256(metadata.sha256, `manifest.files.${path}.sha256`) };
  }

  return {
    schema_version: 1,
    release: {
      release_id: nonEmptyString(release.release_id, "manifest.release.release_id"),
      provider_id: nonEmptyString(release.provider_id, "manifest.release.provider_id"),
      dataset_id: nonEmptyString(release.dataset_id, "manifest.release.dataset_id"),
      retrieved_at: isoDateTime(release.retrieved_at, "manifest.release.retrieved_at"),
      source_checksum: sha256(release.source_checksum, "manifest.release.source_checksum"),
      pipeline_version: nonEmptyString(
        release.pipeline_version,
        "manifest.release.pipeline_version",
      ),
    },
    indicator: {
      indicator_variant_id: nonEmptyString(
        indicator.indicator_variant_id,
        "manifest.indicator.indicator_variant_id",
      ),
      provider_id: nonEmptyString(indicator.provider_id, "manifest.indicator.provider_id"),
      dataset_id: nonEmptyString(indicator.dataset_id, "manifest.indicator.dataset_id"),
      provider_indicator_code: nonEmptyString(
        indicator.provider_indicator_code,
        "manifest.indicator.provider_indicator_code",
      ),
      name: nonEmptyString(indicator.name, "manifest.indicator.name"),
      concept_id: nonEmptyString(indicator.concept_id, "manifest.indicator.concept_id"),
      unit_id: nonEmptyString(indicator.unit_id, "manifest.indicator.unit_id"),
      frequency: enumValue(indicator.frequency, FREQUENCIES, "manifest.indicator.frequency"),
      geography_types: array(
        indicator.geography_types,
        "manifest.indicator.geography_types",
      ).map((item, index) =>
        enumValue(item, GEOGRAPHY_TYPES, `manifest.indicator.geography_types[${index}]`),
      ),
    },
    row_count: nonNegativeInteger(root.row_count, "manifest.row_count"),
    files,
  };
}

export function parseCoverageManifestV1(value: unknown): CoverageManifestV1 {
  const root = object(value, "coverage");
  exactKeys(root, [
    "indicator_variant_id",
    "geography_bits_hex",
    "geography_ids",
    "periods",
    "geography_types",
    "frequency",
    "concept_id",
    "unit_id",
  ], "coverage");
  const geographyIds = array(root.geography_ids, "coverage.geography_ids").map((item, index) =>
    positiveInteger(item, `coverage.geography_ids[${index}]`),
  );
  unique(geographyIds, "coverage.geography_ids");
  const geographyBitsHex = hexInteger(root.geography_bits_hex, "coverage.geography_bits_hex");
  const expectedBits = geographyIds.reduce(
    (bits, geographyId) => bits | (1n << BigInt(geographyId)),
    0n,
  );
  if (BigInt(geographyBitsHex) !== expectedBits) {
    fail("coverage geography bitset does not match geography IDs");
  }
  const periods = array(root.periods, "coverage.periods").map((item, index) =>
    nonEmptyString(item, `coverage.periods[${index}]`),
  );
  unique(periods, "coverage.periods");
  const geographyTypes = array(root.geography_types, "coverage.geography_types").map(
    (item, index) => enumValue(item, GEOGRAPHY_TYPES, `coverage.geography_types[${index}]`),
  );
  unique(geographyTypes, "coverage.geography_types");
  return {
    indicator_variant_id: nonEmptyString(
      root.indicator_variant_id,
      "coverage.indicator_variant_id",
    ),
    geography_bits_hex: geographyBitsHex,
    geography_ids: geographyIds,
    periods,
    geography_types: geographyTypes,
    frequency: enumValue(root.frequency, FREQUENCIES, "coverage.frequency"),
    concept_id: nonEmptyString(root.concept_id, "coverage.concept_id"),
    unit_id: nonEmptyString(root.unit_id, "coverage.unit_id"),
  };
}

export function parseObservationsV1(value: unknown): ObservationV1[] {
  return array(value, "observations").map((item, index) => {
    const observation = object(item, `observations[${index}]`);
    exactKeys(observation, [
      "release_id",
      "indicator_variant_id",
      "geography_id",
      "period_start",
      "period_end",
      "period_label",
      "frequency",
      "unit_id",
      "status",
      "value",
      "provider_quality_flags",
      "system_quality_flags",
    ], `observations[${index}]`);
    const status = enumValue(
      observation.status,
      OBSERVATION_STATUSES,
      `observations[${index}].status`,
    );
    const numericValue = nullableFiniteNumber(observation.value, `observations[${index}].value`);
    const valueRequired = new Set<ObservationStatus>([
      "observed",
      "estimated",
      "modeled",
      "provisional",
      "revised",
    ]).has(status);
    if (valueRequired && numericValue === null) fail(`${status} observations require a value`);
    if (!valueRequired && numericValue !== null) fail(`${status} observations must not contain a value`);

    const periodStart = isoDate(observation.period_start, `observations[${index}].period_start`);
    const periodEnd = isoDate(observation.period_end, `observations[${index}].period_end`);
    if (periodStart > periodEnd) fail(`observations[${index}] period start is after period end`);

    return {
      release_id: nonEmptyString(observation.release_id, `observations[${index}].release_id`),
      indicator_variant_id: nonEmptyString(
        observation.indicator_variant_id,
        `observations[${index}].indicator_variant_id`,
      ),
      geography_id: positiveInteger(observation.geography_id, `observations[${index}].geography_id`),
      period_start: periodStart,
      period_end: periodEnd,
      period_label: nonEmptyString(observation.period_label, `observations[${index}].period_label`),
      frequency: enumValue(observation.frequency, FREQUENCIES, `observations[${index}].frequency`),
      unit_id: nonEmptyString(observation.unit_id, `observations[${index}].unit_id`),
      status,
      value: numericValue,
      provider_quality_flags: stringArray(
        observation.provider_quality_flags,
        `observations[${index}].provider_quality_flags`,
      ),
      system_quality_flags: stringArray(
        observation.system_quality_flags,
        `observations[${index}].system_quality_flags`,
      ),
    };
  });
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
  if (!Number.isInteger(value) || (value as number) <= 0) fail(`${field} must be a positive integer`);
  return value as number;
}

function nonNegativeInteger(value: unknown, field: string): number {
  if (!Number.isInteger(value) || (value as number) < 0) fail(`${field} must be a non-negative integer`);
  return value as number;
}

function nullableFiniteNumber(value: unknown, field: string): number | null {
  if (value === null) return null;
  if (typeof value !== "number" || !Number.isFinite(value)) fail(`${field} must be finite or null`);
  return value;
}

function jsonScalar(value: unknown, field: string): JsonScalar {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean" ||
    (typeof value === "number" && Number.isFinite(value))
  ) {
    return value;
  }
  return fail(`${field} must be a JSON scalar`);
}

function stringArray(value: unknown, field: string): string[] {
  return array(value, field).map((item, index) => nonEmptyString(item, `${field}[${index}]`));
}

function enumValue<T extends string>(value: unknown, allowed: Set<T>, field: string): T {
  if (typeof value !== "string" || !allowed.has(value as T)) fail(`${field} is unsupported`);
  return value as T;
}

function literal<T extends string | number>(value: unknown, expected: T, field: string): T {
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

function sha256(value: unknown, field: string): string {
  const text = nonEmptyString(value, field);
  if (!/^[a-f0-9]{64}$/.test(text)) fail(`${field} must be a lowercase SHA-256 hex digest`);
  return text;
}

function hexInteger(value: unknown, field: string): string {
  const text = nonEmptyString(value, field);
  if (!/^0x[0-9a-f]+$/.test(text)) fail(`${field} must be a lowercase hexadecimal integer`);
  return text;
}

function isoDate(value: unknown, field: string): string {
  const text = nonEmptyString(value, field);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text) || Number.isNaN(Date.parse(`${text}T00:00:00Z`))) {
    fail(`${field} must be an ISO date`);
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
