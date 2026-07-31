import type {
  ObservationV1,
  Operation,
} from "../../../packages/contracts/src/index.js";
import type { CompatibilityResult } from "../../../packages/compatibility/src/index.js";
import type {
  StaticCatalogRelease,
} from "./data.js";
import type { CompatibleObservationSet } from "./explorer.js";
import { correlationSummaryHtml } from "./correlation.js";
import { alignScatterPoints, scatterPlotHtml } from "./scatter.js";
import { trendChartHtml } from "./trend.js";
import { provenanceHtml } from "./provenance.js";

const OPERATION_LABELS: Record<Operation, string> = {
  map: "Map one feature",
  trend: "Compare historical trends",
  table: "Build a data table",
  scatter: "Compare two features",
  ratio: "Calculate a registered ratio",
  correlation: "Explore correlation",
};

const REASON_MESSAGES: Record<string, string> = {
  no_indicators: "Select at least one feature.",
  operation_arity: "The selected operation requires a different number of features.",
  no_shared_geographies: "The selected features have no countries or regions in common.",
  no_shared_periods: "The selected features have no time periods in common.",
  no_shared_geography_type: "The selected features use incompatible geography types.",
  frequency_mismatch: "The selected features use frequencies that are not yet aligned.",
  concept_mismatch: "The requested calculation is not registered for these concepts.",
  unit_mismatch: "The requested calculation is not registered for these units.",
  contextual_comparison: "The features measure different concepts; comparison is contextual, not causal.",
};

export function catalogExplorerShell(release: StaticCatalogRelease): string {
  return `
    <header class="hero">
      <div>
        <p class="eyebrow">Compatibility-first global data explorer</p>
        <h1>WorldInsights</h1>
        <p class="lede">Choose an operation and features. WorldInsights checks shared coverage before downloading observations.</p>
      </div>
      <span class="release-badge">${escapeHtml(release.latest.release_id)}</span>
    </header>
    <main>
      <section class="metrics" aria-label="Catalog summary">
        ${metric("Provider", release.catalog.release.provider_id)}
        ${metric("Features", String(release.catalog.indicators.length))}
        ${metric("Dataset", release.catalog.release.dataset_id)}
        ${metric("Pipeline", release.catalog.release.pipeline_version)}
      </section>
      <section class="explorer-grid">
        <form id="explorer-form" class="panel controls-panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Build an analysis</p>
              <h2>Selection</h2>
            </div>
            <span class="step-badge">Metadata first</span>
          </div>
          <label class="field-label" for="operation-select">Operation</label>
          <select id="operation-select" name="operation">
            ${Object.entries(OPERATION_LABELS)
              .map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`)
              .join("")}
          </select>
          <fieldset class="feature-fieldset">
            <legend>Features</legend>
            <p class="field-help">Coverage files are loaded when the feature count is valid. Values stay unloaded until you choose <strong>Load compatible data</strong>.</p>
            <div class="feature-list">
              ${release.catalog.indicators
                .map((indicator, index) => featureOption(indicator, index))
                .join("")}
            </div>
          </fieldset>
        </form>
        <section class="panel compatibility-panel" aria-labelledby="compatibility-heading">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Compatibility inspector</p>
              <h2 id="compatibility-heading">Selection status</h2>
            </div>
            <span id="compatibility-badge" class="status-badge checking">Checking</span>
          </div>
          <div id="compatibility-status" role="status" aria-live="polite">
            <p>Checking compact coverage metadata…</p>
          </div>
          <div id="scope-controls" class="scope-controls">
            <p class="field-help">Valid countries and periods will appear here.</p>
          </div>
          <button id="load-observations" class="primary-button" type="button" disabled>
            Load compatible data
          </button>
          <p class="privacy-note">No observation files are requested while this button is disabled.</p>
        </section>
      </section>
      <section id="explorer-results" class="panel results-panel" aria-live="polite">
        <p class="eyebrow">Results</p>
        <h2>Nothing loaded yet</h2>
        <p>Choose a valid combination, then load only the compatible observation partitions.</p>
      </section>
    </main>`;
}

export function compatibilityStatusHtml(result: CompatibilityResult): string {
  const title = result.status === "invalid"
    ? "This selection cannot run"
    : result.status === "warning"
      ? "Compatible with important context"
      : "Ready to load";
  const reasons = [...result.blockers, ...result.warnings]
    .map((reason) => REASON_MESSAGES[reason] ?? reason)
    .map((message) => `<li>${escapeHtml(message)}</li>`)
    .join("");

  return `
    <div class="compatibility-summary ${result.status}">
      <h3>${title}</h3>
      <div class="coverage-metrics">
        <div><span>Shared geographies</span><strong>${result.geography_ids.length}</strong></div>
        <div><span>Shared periods</span><strong>${result.periods.length}</strong></div>
        <div><span>Class</span><strong>${escapeHtml(result.compatibility_class)}</strong></div>
      </div>
      ${reasons ? `<ul class="reason-list">${reasons}</ul>` : "<p>Coverage, frequency, concepts, and units passed the current rules.</p>"}
    </div>`;
}

export function compatibleObservationHtml(
  release: StaticCatalogRelease,
  result: CompatibleObservationSet,
): string {
  const selectedIds = [...result.observations.keys()];
  const metadata = new Map(
    release.catalog.indicators.map((indicator) => [indicator.indicator_variant_id, indicator]),
  );
  const rows = alignObservationRows(result.observations);
  const geographyNames = new Map(
    release.catalog.geographies.map((geography) => [geography.geography_id, geography.name]),
  );
  const visualization = result.operation === "correlation"
    ? correlationAnalysisHtml(release, result.observations, selectedIds)
    : result.operation === "scatter"
      ? scatterPlotHtml(release.catalog.indicators, release.catalog.geographies, result.observations)
      : result.operation === "trend"
        ? trendChartHtml(release.catalog.indicators, release.catalog.geographies, result.observations)
        : "";

  return `
    ${visualization}
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Compatible observations</p>
        <h2>${rows.length} aligned row${rows.length === 1 ? "" : "s"}</h2>
      </div>
      <span class="status-badge ${result.compatibility.status}">${escapeHtml(result.compatibility.status)}</span>
    </div>
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th scope="col">Geography</th>
            <th scope="col">Period</th>
            ${selectedIds
              .map((indicatorId) => {
                const indicator = metadata.get(indicatorId);
                return `<th scope="col">${escapeHtml(indicator?.name ?? indicatorId)}<small>${escapeHtml(indicator?.unit_id ?? "")}</small></th>`;
              })
              .join("")}
          </tr>
        </thead>
        <tbody>
          ${rows
            .map((row) => `
              <tr>
                <th scope="row">${escapeHtml(geographyLabel(row.geographyId, geographyNames))}</th>
                <td>${escapeHtml(row.period)}</td>
                ${selectedIds
                  .map((indicatorId) => `<td>${formatNumber(row.values.get(indicatorId) ?? null)}</td>`)
                  .join("")}
              </tr>`)
            .join("")}
        </tbody>
      </table>
    </div>
    ${provenanceHtml(release, selectedIds)}`;
}

export function scopeControlsHtml(
  release: StaticCatalogRelease,
  result: CompatibilityResult,
): string {
  if (result.status === "invalid") {
    return `<p class="field-help">Resolve compatibility blockers before choosing countries and periods.</p>`;
  }
  const geographyNames = new Map(
    release.catalog.geographies.map((geography) => [geography.geography_id, geography.name]),
  );
  const geographyOptions = result.geography_ids
    .map((geographyId) => `
      <label class="scope-option">
        <input type="checkbox" name="scope-geography" value="${geographyId}" checked />
        <span>${escapeHtml(geographyNames.get(geographyId) ?? `Geography ${geographyId}`)}</span>
      </label>`)
    .join("");
  const periodOptions = result.periods
    .map((period) => `
      <label class="scope-option">
        <input type="checkbox" name="scope-period" value="${escapeHtml(period)}" checked />
        <span>${escapeHtml(period)}</span>
      </label>`)
    .join("");
  return `
    <div class="scope-grid">
      <fieldset>
        <legend>Countries and regions</legend>
        <div class="scope-list">${geographyOptions}</div>
      </fieldset>
      <fieldset>
        <legend>Periods</legend>
        <div class="scope-list">${periodOptions}</div>
      </fieldset>
    </div>`;
}

export function statusBadgeClass(status: CompatibilityResult["status"]): string {
  return `status-badge ${status}`;
}

interface AlignedObservationRow {
  geographyId: number;
  period: string;
  values: Map<string, number | null>;
}

function correlationAnalysisHtml(
  release: StaticCatalogRelease,
  observations: ReadonlyMap<string, readonly ObservationV1[]>,
  selectedIds: readonly string[],
): string {
  const xIndicatorId = selectedIds[0];
  const yIndicatorId = selectedIds[1];
  if (selectedIds.length !== 2 || !xIndicatorId || !yIndicatorId) {
    throw new Error("correlation analysis requires exactly two indicators");
  }

  const metadata = new Map(
    release.catalog.indicators.map((indicator) => [indicator.indicator_variant_id, indicator]),
  );
  const xIndicator = metadata.get(xIndicatorId);
  const yIndicator = metadata.get(yIndicatorId);
  if (!xIndicator || !yIndicator) {
    throw new Error("correlation indicator metadata is missing from the catalog");
  }

  const points = alignScatterPoints(observations, xIndicatorId, yIndicatorId);
  return `
    ${correlationSummaryHtml(points, xIndicator.name, yIndicator.name)}
    ${scatterPlotHtml(release.catalog.indicators, release.catalog.geographies, observations)}`;
}

function alignObservationRows(
  observations: ReadonlyMap<string, ObservationV1[]>,
): AlignedObservationRow[] {
  const rows = new Map<string, AlignedObservationRow>();
  for (const [indicatorId, indicatorRows] of observations) {
    for (const observation of indicatorRows) {
      const key = `${observation.geography_id}:${observation.period_label}`;
      let row = rows.get(key);
      if (!row) {
        row = {
          geographyId: observation.geography_id,
          period: observation.period_label,
          values: new Map(),
        };
        rows.set(key, row);
      }
      row.values.set(indicatorId, observation.value);
    }
  }
  return [...rows.values()].sort(
    (left, right) => left.geographyId - right.geographyId || left.period.localeCompare(right.period),
  );
}

function featureOption(
  indicator: StaticCatalogRelease["catalog"]["indicators"][number],
  index: number,
): string {
  const inputId = `indicator-${index}`;
  return `
    <label class="feature-option" for="${inputId}">
      <input
        id="${inputId}"
        type="checkbox"
        name="indicators"
        value="${escapeHtml(indicator.indicator_variant_id)}"
        ${index === 0 ? "checked" : ""}
      />
      <span>
        <strong>${escapeHtml(indicator.name)}</strong>
        <small>${escapeHtml(indicator.provider_id)} · ${escapeHtml(indicator.unit_id)} · ${escapeHtml(indicator.frequency)} · ${indicator.row_count} rows</small>
      </span>
    </label>`;
}

function metric(label: string, value: string): string {
  return `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function geographyLabel(
  geographyId: number,
  names: ReadonlyMap<number, string>,
): string {
  return names.get(geographyId) ?? `Geography ${geographyId}`;
}

function formatNumber(value: number | null): string {
  return value === null
    ? "No data"
    : new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      '"': "&quot;",
    };
    return entities[character] ?? character;
  });
}
