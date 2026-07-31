import type {
  CoverageManifestV1,
  GeographyType,
  Operation,
} from "../../contracts/src/index.js";

export type CompatibilityStatus = "valid" | "warning" | "invalid";
export type CompatibilityClass =
  | "exact"
  | "convertible"
  | "alignable"
  | "contextual"
  | "incompatible";
export type ReasonCode =
  | "no_indicators"
  | "operation_arity"
  | "no_shared_geographies"
  | "no_shared_periods"
  | "no_shared_geography_type"
  | "frequency_mismatch"
  | "concept_mismatch"
  | "unit_mismatch"
  | "contextual_comparison";

export interface CompatibilityResult {
  status: CompatibilityStatus;
  compatibility_class: CompatibilityClass;
  geography_bits_hex: string;
  geography_ids: number[];
  periods: string[];
  geography_types: GeographyType[];
  blockers: ReasonCode[];
  warnings: ReasonCode[];
}

const OPERATION_ARITY: Record<Operation, readonly [number, number | null]> = {
  map: [1, 1],
  trend: [1, null],
  table: [1, null],
  scatter: [2, 2],
  ratio: [2, 2],
  correlation: [2, 2],
};

export function operationAcceptsIndicatorCount(
  operation: Operation,
  count: number,
): boolean {
  const [minimum, maximum] = OPERATION_ARITY[operation];
  return count >= minimum && (maximum === null || count <= maximum);
}

export function convertibleUnitPairKey(left: string, right: string): string {
  return [left, right].sort().join("::");
}

export function evaluateCoverageCompatibility(
  operation: Operation,
  indexes: readonly CoverageManifestV1[],
  convertibleUnitPairs: ReadonlySet<string> = new Set(),
): CompatibilityResult {
  if (indexes.length === 0) return invalidResult("no_indicators");

  if (!operationAcceptsIndicatorCount(operation, indexes.length)) {
    return invalidResult("operation_arity");
  }

  const geographyBits = indexes
    .map((index) => BigInt(index.geography_bits_hex))
    .reduce((left, right) => left & right);
  const periods = intersectSets(indexes.map((index) => new Set(index.periods)));
  const geographyTypes = intersectSets(
    indexes.map((index) => new Set<GeographyType>(index.geography_types)),
  );
  const blockers: ReasonCode[] = [];
  const warnings: ReasonCode[] = [];

  if (geographyBits === 0n) blockers.push("no_shared_geographies");
  if (periods.size === 0) blockers.push("no_shared_periods");
  if (geographyTypes.size === 0) blockers.push("no_shared_geography_type");

  const frequencies = new Set(indexes.map((index) => index.frequency));
  if (frequencies.size > 1) blockers.push("frequency_mismatch");

  const conceptIds = new Set(indexes.map((index) => index.concept_id));
  const unitIds = new Set(indexes.map((index) => index.unit_id));
  let compatibilityClass: CompatibilityClass = "exact";

  if (unitIds.size > 1) {
    const units = [...unitIds];
    const allPairsConvertible = units.every((left) =>
      units.every(
        (right) =>
          left === right || convertibleUnitPairs.has(convertibleUnitPairKey(left, right)),
      ),
    );
    if (allPairsConvertible) {
      compatibilityClass = "convertible";
    } else if (operation === "ratio") {
      blockers.push("unit_mismatch");
    } else {
      warnings.push("unit_mismatch");
      compatibilityClass = "contextual";
    }
  }

  if (operation === "ratio" && conceptIds.size !== 2) {
    blockers.push("concept_mismatch");
  } else if (
    (operation === "scatter" || operation === "correlation") &&
    conceptIds.size > 1
  ) {
    warnings.push("contextual_comparison");
    if (compatibilityClass === "exact") compatibilityClass = "contextual";
  }

  const uniqueBlockers = unique(blockers);
  const uniqueWarnings = unique(warnings);
  return {
    status: uniqueBlockers.length > 0
      ? "invalid"
      : uniqueWarnings.length > 0
        ? "warning"
        : "valid",
    compatibility_class: uniqueBlockers.length > 0 ? "incompatible" : compatibilityClass,
    geography_bits_hex: `0x${geographyBits.toString(16)}`,
    geography_ids: geographyIdsFromBits(geographyBits),
    periods: [...periods].sort(),
    geography_types: [...geographyTypes].sort(),
    blockers: uniqueBlockers,
    warnings: uniqueWarnings,
  };
}

export function geographyIdsFromBits(bits: bigint): number[] {
  if (bits < 0n) throw new RangeError("coverage bitset cannot be negative");
  const result: number[] = [];
  let remaining = bits;
  let position = 0;
  while (remaining > 0n) {
    if ((remaining & 1n) === 1n) result.push(position);
    remaining >>= 1n;
    position += 1;
  }
  return result;
}

function intersectSets<T>(sets: readonly Set<T>[]): Set<T> {
  const first = sets[0];
  if (!first) return new Set();
  const rest = sets.slice(1);
  return new Set([...first].filter((value) => rest.every((set) => set.has(value))));
}

function invalidResult(reason: ReasonCode): CompatibilityResult {
  return {
    status: "invalid",
    compatibility_class: "incompatible",
    geography_bits_hex: "0x0",
    geography_ids: [],
    periods: [],
    geography_types: [],
    blockers: [reason],
    warnings: [],
  };
}

function unique<T>(values: readonly T[]): T[] {
  return [...new Set(values)];
}
