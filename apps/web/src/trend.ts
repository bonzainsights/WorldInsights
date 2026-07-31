import type { ObservationV1 } from "../../../packages/contracts/src/index.js";
import type {
  CatalogGeographyV2,
  CatalogIndicatorV2,
} from "../../../packages/contracts/src/catalog-v2.js";

export interface TrendPoint {
  period: string;
  value: number;
}

export interface TrendSeries {
  geography_id: number;
  segments: TrendPoint[][];
  points: TrendPoint[];
}

interface NumericDomain {
  minimum: number;
  maximum: number;
}

const WIDTH = 820;
const HEIGHT = 440;
const MARGIN = { top: 38, right: 36, bottom: 70, left: 96 } as const;
const SERIES_CLASSES = ["series-a", "series-b", "series-c", "series-d", "series-e"] as const;

export function buildTrendSeries(rows: readonly ObservationV1[]): TrendSeries[] {
  const indicatorIds = new Set(rows.map((row) => row.indicator_variant_id));
  if (indicatorIds.size > 1) throw new Error("trend rows must belong to one indicator");

  const byGeography = new Map<number, ObservationV1[]>();
  const seen = new Set<string>();
  for (const row of rows) {
    const key = `${row.geography_id}\u0000${row.period_label}`;
    if (seen.has(key)) throw new Error(`duplicate trend observation: ${key}`);
    seen.add(key);
    const geographyRows = byGeography.get(row.geography_id) ?? [];
    geographyRows.push(row);
    byGeography.set(row.geography_id, geographyRows);
  }

  return [...byGeography.entries()]
    .sort(([left], [right]) => left - right)
    .map(([geographyId, geographyRows]) => {
      const sorted = [...geographyRows].sort((left, right) => left.period_label.localeCompare(right.period_label));
      const segments: TrendPoint[][] = [];
      const points: TrendPoint[] = [];
      let current: TrendPoint[] = [];

      for (const row of sorted) {
        if (row.value === null || !Number.isFinite(row.value)) {
          if (current.length > 0) segments.push(current);
          current = [];
          continue;
        }
        const point = { period: row.period_label, value: row.value };
        current.push(point);
        points.push(point);
      }
      if (current.length > 0) segments.push(current);
      return { geography_id: geographyId, segments, points };
    });
}

export function trendChartHtml(
  indicators: readonly CatalogIndicatorV2[],
  geographies: readonly CatalogGeographyV2[],
  observations: ReadonlyMap<string, readonly ObservationV1[]>,
): string {
  const indicatorIds = [...observations.keys()];
  if (indicatorIds.length !== 1) {
    return `
      <section class="trend-card" aria-labelledby="trend-heading">
        <h3 id="trend-heading">Historical trend</h3>
        <p>Select exactly one feature to render a shared-unit trend chart. The verified table remains available below.</p>
      </section>`;
  }
  const indicatorId = indicatorIds[0];
  if (!indicatorId) throw new Error("trend indicator ID is missing");
  const indicator = indicators.find((item) => item.indicator_variant_id === indicatorId);
  if (!indicator) throw new Error("trend indicator metadata is missing from the catalog");
  const rows = observations.get(indicatorId) ?? [];
  const series = buildTrendSeries(rows).filter((item) => item.points.length > 0);
  if (series.length === 0) {
    return `
      <section class="trend-card" aria-labelledby="trend-heading">
        <h3 id="trend-heading">Historical trend</h3>
        <p>No observed values are available. Missing values were not converted to zero.</p>
      </section>`;
  }

  const periods = [...new Set(rows.map((row) => row.period_label))].sort();
  const values = series.flatMap((item) => item.points.map((point) => point.value));
  const domain = paddedDomain(values);
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const geographyNames = new Map(geographies.map((geography) => [geography.geography_id, geography.name]));
  const yTicks = ticks(domain, 5);

  const renderedSeries = series.map((item, index) => {
    const seriesClass = SERIES_CLASSES[index % SERIES_CLASSES.length] ?? "series-a";
    const geographyName = geographyNames.get(item.geography_id) ?? `Geography ${item.geography_id}`;
    const lines = item.segments
      .filter((segment) => segment.length > 1)
      .map((segment) => `<polyline class="trend-line ${seriesClass}" points="${segment
        .map((point) => `${coordinate(xPosition(point.period, periods, plotWidth))},${coordinate(yPosition(point.value, domain, plotHeight))}`)
        .join(" ")}" />`)
      .join("");
    const points = item.points.map((point) => {
      const x = xPosition(point.period, periods, plotWidth);
      const y = yPosition(point.value, domain, plotHeight);
      const accessible = `${geographyName}, ${point.period}. ${indicator.name}: ${formatValue(point.value)} ${indicator.unit_id}.`;
      return `<circle class="trend-point ${seriesClass}" cx="${coordinate(x)}" cy="${coordinate(y)}" r="6" tabindex="0" aria-label="${escapeHtml(accessible)}"><title>${escapeHtml(accessible)}</title></circle>`;
    }).join("");
    return `${lines}${points}`;
  }).join("");

  const legend = series.map((item, index) => {
    const seriesClass = SERIES_CLASSES[index % SERIES_CLASSES.length] ?? "series-a";
    const geographyName = geographyNames.get(item.geography_id) ?? `Geography ${item.geography_id}`;
    return `<li><span class="legend-swatch ${seriesClass}" aria-hidden="true"></span>${escapeHtml(geographyName)}</li>`;
  }).join("");

  return `
    <style>
      .trend-card { margin-bottom: 2rem; padding-bottom: 1.75rem; border-bottom: 1px solid #1e3552; }
      .trend-chart { display: block; width: 100%; min-width: 42rem; height: auto; border: 1px solid #203851; border-radius: .9rem; background: #081522; }
      .trend-line { fill: none; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
      .trend-point { stroke: #081522; stroke-width: 3; }
      .trend-point:focus { outline: none; stroke: #fff0a6; stroke-width: 5; }
      .series-a { stroke: #63bcff; fill: #63bcff; background: #63bcff; }
      .series-b { stroke: #70e4c5; fill: #70e4c5; background: #70e4c5; }
      .series-c { stroke: #f3c969; fill: #f3c969; background: #f3c969; }
      .series-d { stroke: #d5a6ff; fill: #d5a6ff; background: #d5a6ff; }
      .series-e { stroke: #ff9eaa; fill: #ff9eaa; background: #ff9eaa; }
      .chart-legend { display: flex; flex-wrap: wrap; gap: .65rem 1rem; margin: 0 0 1rem; padding: 0; list-style: none; color: #c8d7e8; }
      .chart-legend li { display: flex; gap: .45rem; align-items: center; }
      .legend-swatch { width: .85rem; height: .85rem; border-radius: 999px; }
      @media (max-width: 720px) { .trend-card { overflow-x: auto; } }
    </style>
    <section class="trend-card" aria-labelledby="trend-heading">
      <div class="chart-heading">
        <div>
          <p class="eyebrow">Historical comparison</p>
          <h3 id="trend-heading">${escapeHtml(indicator.name)}</h3>
        </div>
        <span>${escapeHtml(`${periods[0] ?? ""}–${periods.at(-1) ?? ""}`)}</span>
      </div>
      <ul class="chart-legend" aria-label="Country series">${legend}</ul>
      <svg class="trend-chart" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-labelledby="trend-svg-title trend-svg-description">
        <title id="trend-svg-title">${escapeHtml(indicator.name)} over time</title>
        <desc id="trend-svg-description">Lines compare selected countries across available periods. Missing values create gaps.</desc>
        ${periods.map((period) => verticalGridLine(period, periods, plotHeight)).join("")}
        ${yTicks.map((tick) => horizontalGridLine(tick, domain, plotWidth)).join("")}
        <line class="axis-line" x1="${MARGIN.left}" y1="${MARGIN.top + plotHeight}" x2="${MARGIN.left + plotWidth}" y2="${MARGIN.top + plotHeight}" />
        <line class="axis-line" x1="${MARGIN.left}" y1="${MARGIN.top}" x2="${MARGIN.left}" y2="${MARGIN.top + plotHeight}" />
        ${renderedSeries}
        <text class="axis-title" transform="translate(22 ${HEIGHT / 2}) rotate(-90)" text-anchor="middle">${escapeHtml(indicator.unit_id)}</text>
      </svg>
      <p class="chart-note">Missing values create line gaps and are never treated as zero.</p>
    </section>`;
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

function xPosition(period: string, periods: readonly string[], plotWidth: number): number {
  const index = periods.indexOf(period);
  if (index < 0) throw new Error(`trend period is not declared: ${period}`);
  if (periods.length === 1) return MARGIN.left + plotWidth / 2;
  return MARGIN.left + (index / (periods.length - 1)) * plotWidth;
}

function yPosition(value: number, domain: NumericDomain, plotHeight: number): number {
  return MARGIN.top + plotHeight - ((value - domain.minimum) / (domain.maximum - domain.minimum)) * plotHeight;
}

function verticalGridLine(period: string, periods: readonly string[], plotHeight: number): string {
  const x = xPosition(period, periods, WIDTH - MARGIN.left - MARGIN.right);
  return `<g class="chart-grid"><line x1="${coordinate(x)}" y1="${MARGIN.top}" x2="${coordinate(x)}" y2="${MARGIN.top + plotHeight}" /><text x="${coordinate(x)}" y="${MARGIN.top + plotHeight + 25}" text-anchor="middle">${escapeHtml(period)}</text></g>`;
}

function horizontalGridLine(value: number, domain: NumericDomain, plotWidth: number): string {
  const y = yPosition(value, domain, HEIGHT - MARGIN.top - MARGIN.bottom);
  return `<g class="chart-grid"><line x1="${MARGIN.left}" y1="${coordinate(y)}" x2="${MARGIN.left + plotWidth}" y2="${coordinate(y)}" /><text x="${MARGIN.left - 13}" y="${coordinate(y + 4)}" text-anchor="end">${escapeHtml(formatCompact(value))}</text></g>`;
}

function coordinate(value: number): string {
  return value.toFixed(2);
}

function formatCompact(value: number): string {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
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
