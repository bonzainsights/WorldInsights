import type { ObservationV1 } from "../../../packages/contracts/src/index.js";
import type {
  CatalogGeographyV2,
  CatalogIndicatorV2,
} from "../../../packages/contracts/src/catalog-v2.js";
import { geometryPath, type WorldTopology } from "./choropleth.js";

const WIDTH = 960;
const HEIGHT = 500;

interface MapValue {
  geographyId: number;
  name: string;
  value: number | null;
}

interface NumericDomain {
  minimum: number;
  maximum: number;
}

export function choroplethMapHtmlM49(
  indicators: readonly CatalogIndicatorV2[],
  geographies: readonly CatalogGeographyV2[],
  observations: ReadonlyMap<string, readonly ObservationV1[]>,
  topology: WorldTopology,
): string {
  const indicatorIds = [...observations.keys()];
  if (indicatorIds.length !== 1) {
    throw new Error("a choropleth requires exactly one indicator");
  }
  const indicatorId = indicatorIds[0];
  if (!indicatorId) throw new Error("map indicator ID is missing");
  const indicator = indicators.find((item) => item.indicator_variant_id === indicatorId);
  if (!indicator) throw new Error("map indicator metadata is missing from the catalog");

  const rows = observations.get(indicatorId) ?? [];
  const periods = [...new Set(rows.map((row) => row.period_label))].sort();
  const period = periods.at(-1);
  if (!period) throw new Error("map observations contain no period");

  const geographyById = new Map(geographies.map((item) => [item.geography_id, item]));
  const seen = new Set<number>();
  const valuesByM49 = new Map<string, MapValue>();

  for (const row of rows) {
    if (row.period_label !== period) continue;
    if (seen.has(row.geography_id)) {
      throw new Error(`duplicate map observation for geography: ${row.geography_id}`);
    }
    seen.add(row.geography_id);

    const geography = geographyById.get(row.geography_id);
    if (!geography) throw new Error(`map geography is absent from catalog: ${row.geography_id}`);
    if (geography.geography_type !== "country" && geography.geography_type !== "territory") {
      throw new Error(`map geography must be a country or territory: ${geography.canonical_code}`);
    }
    const m49 = m49FromGeographyId(geography.geography_id);
    valuesByM49.set(m49, {
      geographyId: geography.geography_id,
      name: geography.name,
      value: row.value,
    });
  }

  const observedValues = [...valuesByM49.values()]
    .map((item) => item.value)
    .filter((value): value is number => value !== null && Number.isFinite(value));
  const domain = numericDomain(observedValues);
  const paths = topology.objects.countries.geometries
    .map((geometry) => {
      const mapValue = valuesByM49.get(geometry.id);
      const path = geometryPath(topology, geometry);
      if (!mapValue) {
        return `<path class="map-country no-coverage" d="${path}" aria-hidden="true"></path>`;
      }
      if (mapValue.value === null) {
        const label = `${mapValue.name}, ${period}. ${indicator.name}: no data`;
        return `<path class="map-country missing-data" d="${path}" tabindex="0" role="img" aria-label="${escapeHtml(label)}"><title>${escapeHtml(label)}</title></path>`;
      }
      const label = `${mapValue.name}, ${period}. ${indicator.name}: ${formatNumber(mapValue.value)} ${indicator.unit_id}`;
      return `<path class="map-country has-data" d="${path}" fill="${valueFill(mapValue.value, domain)}" tabindex="0" role="img" aria-label="${escapeHtml(label)}"><title>${escapeHtml(label)}</title></path>`;
    })
    .join("");

  const minimum = domain ? formatNumber(domain.minimum) : "No observed values";
  const maximum = domain ? formatNumber(domain.maximum) : "No observed values";
  return `
    <style>
      .choropleth-card { margin-bottom: 2rem; padding-bottom: 1.75rem; border-bottom: 1px solid #1e3552; }
      .choropleth-map { display: block; width: 100%; height: auto; border: 1px solid #203851; border-radius: .9rem; background: #081522; }
      .map-country { stroke: #081522; stroke-width: .7; vector-effect: non-scaling-stroke; }
      .map-country.no-coverage { fill: #17283a; }
      .map-country.missing-data { fill: #526171; }
      .map-country.has-data:focus { outline: none; stroke: #fff0a6; stroke-width: 3; }
      .map-legend { display: flex; flex-wrap: wrap; gap: .6rem 1rem; align-items: center; margin: .8rem 0 0; color: #b7c9dc; font-size: .85rem; }
      .map-gradient { width: min(18rem, 60vw); height: .75rem; border-radius: 999px; background: linear-gradient(90deg, hsl(205 78% 72%), hsl(205 88% 38%)); }
      .map-swatch { width: .8rem; height: .8rem; border-radius: .15rem; background: #526171; }
      .map-source { color: #8fa6bf; font-size: .82rem; line-height: 1.5; }
    </style>
    <section class="choropleth-card" aria-labelledby="choropleth-heading">
      <div class="chart-heading">
        <div>
          <p class="eyebrow">Country choropleth</p>
          <h3 id="choropleth-heading">${escapeHtml(indicator.name)}</h3>
        </div>
        <span>latest selected period (${escapeHtml(period)})</span>
      </div>
      <svg class="choropleth-map" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-labelledby="map-title map-description">
        <title id="map-title">${escapeHtml(indicator.name)} by country in ${escapeHtml(period)}</title>
        <desc id="map-description">Countries with selected data are shaded by value. Countries without loaded data are neutral. Exact values remain available in the table below.</desc>
        ${paths}
      </svg>
      <div class="map-legend" aria-label="Map legend">
        <span>${minimum}</span><span class="map-gradient" aria-hidden="true"></span><span>${maximum}</span>
        <span class="map-swatch" aria-hidden="true"></span><span>Missing data</span>
      </div>
      <p class="map-source">Geometry: world-atlas 2.0.2, derived from Natural Earth 1:110m. Geography joins use canonical UN M49 IDs. The table remains the authoritative accessible fallback.</p>
    </section>`;
}

export function m49FromGeographyId(geographyId: number): string {
  if (!Number.isInteger(geographyId) || geographyId <= 0 || geographyId > 999) {
    throw new Error(`country geography ID is not a valid M49 code: ${geographyId}`);
  }
  return String(geographyId).padStart(3, "0");
}

function numericDomain(values: readonly number[]): NumericDomain | null {
  if (values.length === 0) return null;
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  return { minimum, maximum };
}

function valueFill(value: number, domain: NumericDomain | null): string {
  if (!domain || domain.minimum === domain.maximum) return "hsl(205 82% 50%)";
  const fraction = Math.max(0, Math.min(1, (value - domain.minimum) / (domain.maximum - domain.minimum)));
  const lightness = 72 - fraction * 34;
  return `hsl(205 84% ${lightness.toFixed(2)}%)`;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(value);
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character] ?? character);
}
