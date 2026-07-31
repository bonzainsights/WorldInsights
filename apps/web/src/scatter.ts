import type { ObservationV1 } from "../../../packages/contracts/src/index.js";
import type {
  CatalogGeographyV2,
  CatalogIndicatorV2,
} from "../../../packages/contracts/src/catalog-v2.js";

export interface ScatterPoint {
  geography_id: number;
  period: string;
  x: number;
  y: number;
}

interface NumericDomain {
  minimum: number;
  maximum: number;
}

const WIDTH = 760;
const HEIGHT = 430;
const MARGIN = { top: 34, right: 34, bottom: 76, left: 94 } as const;

export function alignScatterPoints(
  observations: ReadonlyMap<string, readonly ObservationV1[]>,
  xIndicatorId: string,
  yIndicatorId: string,
): ScatterPoint[] {
  const xRows = observations.get(xIndicatorId);
  const yRows = observations.get(yIndicatorId);
  if (!xRows || !yRows) return [];

  const xByKey = indexValues(xRows, xIndicatorId);
  const yByKey = indexValues(yRows, yIndicatorId);
  const points: ScatterPoint[] = [];

  for (const [key, xValue] of xByKey) {
    const yValue = yByKey.get(key);
    if (yValue === undefined) continue;
    const [geographyText, period] = splitKey(key);
    points.push({
      geography_id: Number(geographyText),
      period,
      x: xValue,
      y: yValue,
    });
  }

  return points.sort(
    (left, right) => left.period.localeCompare(right.period) || left.geography_id - right.geography_id,
  );
}

export function scatterPlotHtml(
  indicators: readonly CatalogIndicatorV2[],
  geographies: readonly CatalogGeographyV2[],
  observations: ReadonlyMap<string, readonly ObservationV1[]>,
): string {
  const indicatorIds = [...observations.keys()];
  if (indicatorIds.length !== 2) {
    throw new Error("scatter visualization requires exactly two indicators");
  }
  const xIndicatorId = indicatorIds[0];
  const yIndicatorId = indicatorIds[1];
  if (!xIndicatorId || !yIndicatorId) {
    throw new Error("scatter visualization requires exactly two indicators");
  }

  const metadata = new Map(indicators.map((indicator) => [indicator.indicator_variant_id, indicator]));
  const xIndicator = metadata.get(xIndicatorId);
  const yIndicator = metadata.get(yIndicatorId);
  if (!xIndicator || !yIndicator) {
    throw new Error("scatter indicator metadata is missing from the catalog");
  }

  const points = alignScatterPoints(observations, xIndicatorId, yIndicatorId);
  if (points.length === 0) {
    return `
      <section class="scatter-card" aria-labelledby="scatter-heading">
        <h3 id="scatter-heading">Scatter comparison</h3>
        <p>No complete country-period pairs are available. Missing values were not converted to zero.</p>
      </section>`;
  }

  const geographyNames = new Map(geographies.map((geography) => [geography.geography_id, geography.name]));
  const xDomain = paddedDomain(points.map((point) => point.x));
  const yDomain = paddedDomain(points.map((point) => point.y));
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const xTicks = ticks(xDomain, 5);
  const yTicks = ticks(yDomain, 5);

  const circles = points.map((point) => {
    const cx = scale(point.x, xDomain, MARGIN.left, MARGIN.left + plotWidth);
    const cy = scale(point.y, yDomain, MARGIN.top + plotHeight, MARGIN.top);
    const geography = geographyNames.get(point.geography_id) ?? `Geography ${point.geography_id}`;
    const accessible = `${geography}, ${point.period}. ${xIndicator.name}: ${formatValue(point.x)} ${xIndicator.unit_id}. ${yIndicator.name}: ${formatValue(point.y)} ${yIndicator.unit_id}.`;
    return `
      <g class="scatter-point">
        <circle cx="${coordinate(cx)}" cy="${coordinate(cy)}" r="7" tabindex="0" aria-label="${escapeHtml(accessible)}">
          <title>${escapeHtml(accessible)}</title>
        </circle>
        <text x="${coordinate(cx + 11)}" y="${coordinate(cy - 9)}">${escapeHtml(geography)}</text>
      </g>`;
  }).join("");

  return `
    <section class="scatter-card" aria-labelledby="scatter-heading">
      <div class="chart-heading">
        <div>
          <p class="eyebrow">Cross-feature comparison</p>
          <h3 id="scatter-heading">${escapeHtml(yIndicator.name)} versus ${escapeHtml(xIndicator.name)}</h3>
        </div>
        <span>${points.length} complete pair${points.length === 1 ? "" : "s"}</span>
      </div>
      <svg class="scatter-chart" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-labelledby="scatter-svg-title scatter-svg-description">
        <title id="scatter-svg-title">${escapeHtml(yIndicator.name)} versus ${escapeHtml(xIndicator.name)}</title>
        <desc id="scatter-svg-description">Each point is one country and period with non-missing values for both selected indicators.</desc>
        ${xTicks.map((tick) => verticalGridLine(tick, xDomain, plotHeight)).join("")}
        ${yTicks.map((tick) => horizontalGridLine(tick, yDomain, plotWidth)).join("")}
        <line class="axis-line" x1="${MARGIN.left}" y1="${MARGIN.top + plotHeight}" x2="${MARGIN.left + plotWidth}" y2="${MARGIN.top + plotHeight}" />
        <line class="axis-line" x1="${MARGIN.left}" y1="${MARGIN.top}" x2="${MARGIN.left}" y2="${MARGIN.top + plotHeight}" />
        ${circles}
        <text class="axis-title" x="${WIDTH / 2}" y="${HEIGHT - 18}" text-anchor="middle">${escapeHtml(`${xIndicator.name} (${xIndicator.unit_id})`)}</text>
        <text class="axis-title" transform="translate(22 ${HEIGHT / 2}) rotate(-90)" text-anchor="middle">${escapeHtml(`${yIndicator.name} (${yIndicator.unit_id})`)}</text>
      </svg>
      <p class="chart-note">Only complete pairs are plotted. The chart describes association and does not imply causation.</p>
    </section>`;
}

function indexValues(rows: readonly ObservationV1[], indicatorId: string): Map<string, number> {
  const values = new Map<string, number>();
  for (const row of rows) {
    if (row.indicator_variant_id !== indicatorId) {
      throw new Error(`observation indicator mismatch: expected ${indicatorId}`);
    }
    if (row.value === null || !Number.isFinite(row.value)) continue;
    const key = observationKey(row);
    if (values.has(key)) throw new Error(`duplicate scatter observation: ${key}`);
    values.set(key, row.value);
  }
  return values;
}

function observationKey(row: ObservationV1): string {
  return `${row.geography_id}\u0000${row.period_label}`;
}

function splitKey(key: string): [string, string] {
  const separator = key.indexOf("\u0000");
  if (separator < 1) throw new Error("invalid scatter observation key");
  return [key.slice(0, separator), key.slice(separator + 1)];
}

function paddedDomain(values: readonly number[]): NumericDomain {
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  if (minimum === maximum) {
    const padding = Math.max(Math.abs(minimum) * 0.08, 1);
    return { minimum: minimum - padding, maximum: maximum + padding };
  }
  const padding = (maximum - minimum) * 0.08;
  return { minimum: minimum - padding, maximum: maximum + padding };
}

function ticks(domain: NumericDomain, count: number): number[] {
  const interval = (domain.maximum - domain.minimum) / (count - 1);
  return Array.from({ length: count }, (_, index) => domain.minimum + interval * index);
}

function scale(value: number, domain: NumericDomain, start: number, end: number): number {
  return start + ((value - domain.minimum) / (domain.maximum - domain.minimum)) * (end - start);
}

function verticalGridLine(value: number, domain: NumericDomain, plotHeight: number): string {
  const x = scale(value, domain, MARGIN.left, WIDTH - MARGIN.right);
  return `<g class="chart-grid"><line x1="${coordinate(x)}" y1="${MARGIN.top}" x2="${coordinate(x)}" y2="${MARGIN.top + plotHeight}" /><text x="${coordinate(x)}" y="${MARGIN.top + plotHeight + 25}" text-anchor="middle">${escapeHtml(formatCompact(value))}</text></g>`;
}

function horizontalGridLine(value: number, domain: NumericDomain, plotWidth: number): string {
  const y = scale(value, domain, HEIGHT - MARGIN.bottom, MARGIN.top);
  return `<g class="chart-grid"><line x1="${MARGIN.left}" y1="${coordinate(y)}" x2="${MARGIN.left + plotWidth}" y2="${coordinate(y)}" /><text x="${MARGIN.left - 13}" y="${coordinate(y + 4)}" text-anchor="end">${escapeHtml(formatCompact(value))}</text></g>`;
}

function coordinate(value: number): string {
  return value.toFixed(2);
}

function formatCompact(value: number): string {
  return new Intl.NumberFormat("en", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatValue(value: number): string {
  return new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(value);
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
