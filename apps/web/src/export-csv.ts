import type { ObservationV1 } from "../../../packages/contracts/src/index.js";
import type { StaticCatalogRelease } from "./data.js";
import type { CompatibleObservationSet } from "./explorer.js";

interface ExportRow {
  geographyId: number;
  period: string;
  values: Map<string, number | null>;
}

export function compatibleObservationsCsv(
  release: StaticCatalogRelease,
  result: CompatibleObservationSet,
): string {
  const indicatorIds = [...result.observations.keys()];
  if (indicatorIds.length === 0) throw new Error("CSV export requires at least one indicator");

  const indicatorById = new Map(
    release.catalog.indicators.map((indicator) => [indicator.indicator_variant_id, indicator]),
  );
  for (const indicatorId of indicatorIds) {
    if (!indicatorById.has(indicatorId)) {
      throw new Error(`CSV indicator is not in the catalog: ${indicatorId}`);
    }
  }

  const geographyById = new Map(
    release.catalog.geographies.map((geography) => [geography.geography_id, geography]),
  );
  const rows = alignRows(result.observations);
  const header = [
    "release_id",
    "provider_id",
    "dataset_id",
    "geography_id",
    "geography_code",
    "geography_name",
    "period",
    ...indicatorIds,
  ];
  const lines = [header.map(csvCell).join(",")];

  for (const row of rows) {
    const geography = geographyById.get(row.geographyId);
    if (!geography) throw new Error(`CSV geography is not in the catalog: ${row.geographyId}`);
    lines.push([
      release.catalog.release.release_id,
      release.catalog.release.provider_id,
      release.catalog.release.dataset_id,
      String(row.geographyId),
      geography.canonical_code,
      geography.name,
      row.period,
      ...indicatorIds.map((indicatorId) => numericCell(row.values.get(indicatorId) ?? null)),
    ].map(csvCell).join(","));
  }

  return `${lines.join("\n")}\n`;
}

export function csvFileName(release: StaticCatalogRelease): string {
  return `${safeFileSegment(release.catalog.release.release_id)}-observations.csv`;
}

export function downloadCsv(fileName: string, content: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }));
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    anchor.hidden = true;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(url);
  }
}

function alignRows(
  observations: ReadonlyMap<string, readonly ObservationV1[]>,
): ExportRow[] {
  const rows = new Map<string, ExportRow>();
  for (const [indicatorId, indicatorRows] of observations) {
    for (const observation of indicatorRows) {
      if (observation.indicator_variant_id !== indicatorId) {
        throw new Error(`CSV observation indicator mismatch: expected ${indicatorId}`);
      }
      const key = `${observation.geography_id}\u0000${observation.period_label}`;
      let row = rows.get(key);
      if (!row) {
        row = {
          geographyId: observation.geography_id,
          period: observation.period_label,
          values: new Map(),
        };
        rows.set(key, row);
      }
      if (row.values.has(indicatorId)) {
        throw new Error(`duplicate CSV observation: ${observation.geography_id}:${observation.period_label}:${indicatorId}`);
      }
      row.values.set(indicatorId, observation.value);
    }
  }
  return [...rows.values()].sort(
    (left, right) => left.geographyId - right.geographyId || left.period.localeCompare(right.period),
  );
}

function numericCell(value: number | null): string {
  if (value === null) return "";
  if (!Number.isFinite(value)) throw new Error("CSV values must be finite or null");
  return String(value);
}

function csvCell(value: string): string {
  if (/[",\r\n]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

function safeFileSegment(value: string): string {
  const safe = value.replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  return safe || "worldinsights";
}
