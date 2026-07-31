import type { ObservationV1 } from "../../../packages/contracts/src/index.js";
import type {
  CatalogGeographyV2,
  CatalogIndicatorV2,
} from "../../../packages/contracts/src/catalog-v2.js";
import type { FetchLike } from "./data.js";

export const WORLD_ATLAS_URL =
  "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json";

const WIDTH = 960;
const HEIGHT = 500;
const M49_BY_ISO3: Readonly<Record<string, string>> = {
  DEU: "276",
  NPL: "524",
  USA: "840",
};

interface TopologyTransform {
  scale: readonly [number, number];
  translate: readonly [number, number];
}

interface TopologyGeometry {
  type: "Polygon" | "MultiPolygon";
  id: string;
  properties: { name: string };
  arcs: unknown;
}

export interface WorldTopology {
  type: "Topology";
  transform: TopologyTransform;
  arcs: readonly (readonly (readonly [number, number])[])[];
  objects: {
    countries: {
      type: "GeometryCollection";
      geometries: readonly TopologyGeometry[];
    };
  };
}

interface MapValue {
  geographyId: number;
  canonicalCode: string;
  name: string;
  value: number | null;
}

export async function loadWorldTopology(
  fetcher: FetchLike = globalThis.fetch.bind(globalThis),
): Promise<WorldTopology> {
  const response = await fetcher(WORLD_ATLAS_URL);
  if (!response.ok) throw new Error(`world geometry request failed with HTTP ${response.status}`);
  return parseWorldTopology(await response.json());
}

export function parseWorldTopology(value: unknown): WorldTopology {
  const root = object(value, "topology");
  if (root.type !== "Topology") throw new Error("world geometry must be Topology");

  const transform = object(root.transform, "topology.transform");
  const scale = numericPair(transform.scale, "topology.transform.scale");
  const translate = numericPair(transform.translate, "topology.transform.translate");

  if (!Array.isArray(root.arcs) || root.arcs.length === 0) {
    throw new Error("topology.arcs must be a non-empty array");
  }
  const arcs = root.arcs.map((arc, arcIndex) => {
    if (!Array.isArray(arc) || arc.length === 0) {
      throw new Error(`topology.arcs[${arcIndex}] must be a non-empty array`);
    }
    return arc.map((point, pointIndex) =>
      numericPair(point, `topology.arcs[${arcIndex}][${pointIndex}]`),
    );
  });

  const objects = object(root.objects, "topology.objects");
  const countries = object(objects.countries, "topology.objects.countries");
  if (countries.type !== "GeometryCollection" || !Array.isArray(countries.geometries)) {
    throw new Error("topology countries must be a GeometryCollection");
  }
  const geometries = countries.geometries.map((item, index): TopologyGeometry => {
    const geometry = object(item, `topology.countries[${index}]`);
    if (geometry.type !== "Polygon" && geometry.type !== "MultiPolygon") {
      throw new Error(`unsupported country geometry type: ${String(geometry.type)}`);
    }
    const id = String(geometry.id ?? "").padStart(3, "0");
    if (!/^\d{3}$/.test(id)) throw new Error("country geometry ID must be an M49 code");
    const properties = object(geometry.properties, `topology.countries[${index}].properties`);
    const name = nonEmptyString(properties.name, `topology.countries[${index}].properties.name`);
    validateGeometryArcs(geometry.type, geometry.arcs, `topology.countries[${index}].arcs`);
    return { type: geometry.type, id, properties: { name }, arcs: geometry.arcs };
  });
  if (geometries.length === 0) throw new Error("topology has no country geometries");

  return {
    type: "Topology",
    transform: { scale, translate },
    arcs,
    objects: { countries: { type: "GeometryCollection", geometries } },
  };
}

export function choroplethMapHtml(
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
    const m49 = M49_BY_ISO3[geography.canonical_code];
    if (!m49) throw new Error(`map geometry is not registered for ${geography.canonical_code}`);
    valuesByM49.set(m49, {
      geographyId: geography.geography_id,
      canonicalCode: geography.canonical_code,
      name: geography.name,
      value: row.value,
    });
  }

  const observedValues = [...valuesByM49.values()]
    .map((item) => item.value)
    .filter((value): value is number => value !== null && Number.isFinite(value));
  const domain = numericDomain(observedValues);
  const paths = topology.objects.countries.geometries
    .map((geometry) => countryPathHtml(topology, geometry, valuesByM49.get(geometry.id), indicator, period, domain))
    .join("");

  const minLabel = domain ? formatNumber(domain.minimum) : "No observed values";
  const maxLabel = domain ? formatNumber(domain.maximum) : "No observed values";
  return `
    <style>
      .choropleth-card { margin-bottom: 2rem; padding-bottom: 1.75rem; border-bottom: 1px solid #1e3552; }
      .choropleth-map { display: block; width: 100%; height: auto; border: 1px solid #203851; border-radius: .9rem; background: #081522; }
      .map-country { stroke: #081522; stroke-width: .7; vector-effect: non-scaling-stroke; }
      .map-country.no-coverage { fill: #17283a; }
      .map-country.missing-data { fill: #526171; }
      .map-country.has-data { cursor: default; }
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
        <span>${escapeHtml(period)}</span>
      </div>
      <svg class="choropleth-map" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-labelledby="map-title map-description">
        <title id="map-title">${escapeHtml(indicator.name)} by country in ${escapeHtml(period)}</title>
        <desc id="map-description">Countries with selected data are shaded by value. Countries without loaded data are shown in neutral gray. Exact values are available in the table below.</desc>
        ${paths}
      </svg>
      <div class="map-legend" aria-label="Map legend">
        <span>${escapeHtml(minLabel)}</span><span class="map-gradient" aria-hidden="true"></span><span>${escapeHtml(maxLabel)}</span>
        <span class="map-swatch" aria-hidden="true"></span><span>Missing or not selected</span>
      </div>
      <p class="chart-note">When multiple periods are selected, the map uses the latest selected period (${escapeHtml(period)}). Missing values are never converted to zero.</p>
      <p class="map-source">Geometry: world-atlas 2.0.2, derived from Natural Earth 1:110m boundaries. The exact observation table remains the authoritative accessible fallback.</p>
    </section>`;
}

function countryPathHtml(
  topology: WorldTopology,
  geometry: TopologyGeometry,
  mapValue: MapValue | undefined,
  indicator: CatalogIndicatorV2,
  period: string,
  domain: { minimum: number; maximum: number } | null,
): string {
  const path = geometryPath(topology, geometry);
  if (!mapValue) {
    return `<path class="map-country no-coverage" d="${path}" aria-hidden="true" />`;
  }
  if (mapValue.value === null || !Number.isFinite(mapValue.value)) {
    const label = `${mapValue.name}, ${period}. ${indicator.name}: no data.`;
    return `<path class="map-country missing-data" d="${path}" tabindex="0" role="img" aria-label="${escapeHtml(label)}"><title>${escapeHtml(label)}</title></path>`;
  }
  const fill = mapColor(mapValue.value, domain);
  const label = `${mapValue.name}, ${period}. ${indicator.name}: ${formatNumber(mapValue.value)} ${indicator.unit_id}.`;
  return `<path class="map-country has-data" d="${path}" fill="${fill}" tabindex="0" role="img" data-geography-id="${mapValue.geographyId}" data-country-code="${mapValue.canonicalCode}" aria-label="${escapeHtml(label)}"><title>${escapeHtml(label)}</title></path>`;
}

export function geometryPath(topology: WorldTopology, geometry: TopologyGeometry): string {
  const polygons = geometry.type === "Polygon"
    ? [geometry.arcs as number[][]]
    : geometry.arcs as number[][][];
  return polygons
    .flatMap((polygon) => polygon.map((ring) => ringPath(topology, ring)))
    .join(" ");
}

function ringPath(topology: WorldTopology, ring: readonly number[]): string {
  const points: [number, number][] = [];
  for (const arcIndex of ring) {
    const arc = decodedArc(topology, arcIndex);
    if (points.length > 0 && arc.length > 0) arc.shift();
    points.push(...arc);
  }
  if (points.length < 3) throw new Error("country ring must contain at least three points");
  return points
    .map(([longitude, latitude], index) => {
      const [x, y] = project(longitude, latitude);
      return `${index === 0 ? "M" : "L"}${coordinate(x)},${coordinate(y)}`;
    })
    .join("") + "Z";
}

function decodedArc(topology: WorldTopology, signedIndex: number): [number, number][] {
  if (!Number.isInteger(signedIndex)) throw new Error("topology arc index must be an integer");
  const arcIndex = signedIndex < 0 ? ~signedIndex : signedIndex;
  const source = topology.arcs[arcIndex];
  if (!source) throw new Error(`topology arc is missing: ${arcIndex}`);
  let x = 0;
  let y = 0;
  const decoded = source.map(([deltaX, deltaY]): [number, number] => {
    x += deltaX;
    y += deltaY;
    return [
      x * topology.transform.scale[0] + topology.transform.translate[0],
      y * topology.transform.scale[1] + topology.transform.translate[1],
    ];
  });
  return signedIndex < 0 ? decoded.reverse() : decoded;
}

function project(longitude: number, latitude: number): [number, number] {
  return [((longitude + 180) / 360) * WIDTH, ((90 - latitude) / 180) * HEIGHT];
}

function numericDomain(values: readonly number[]): { minimum: number; maximum: number } | null {
  if (values.length === 0) return null;
  return { minimum: Math.min(...values), maximum: Math.max(...values) };
}

function mapColor(value: number, domain: { minimum: number; maximum: number } | null): string {
  if (!domain || domain.minimum === domain.maximum) return "hsl(205 84% 52%)";
  const normalized = (value - domain.minimum) / (domain.maximum - domain.minimum);
  const lightness = 72 - normalized * 34;
  return `hsl(205 84% ${lightness.toFixed(1)}%)`;
}

function validateGeometryArcs(type: TopologyGeometry["type"], value: unknown, field: string): void {
  if (!Array.isArray(value) || value.length === 0) throw new Error(`${field} must be non-empty`);
  const polygons = type === "Polygon" ? [value] : value;
  for (const [polygonIndex, polygon] of polygons.entries()) {
    if (!Array.isArray(polygon) || polygon.length === 0) {
      throw new Error(`${field}[${polygonIndex}] must contain rings`);
    }
    for (const [ringIndex, ring] of polygon.entries()) {
      if (!Array.isArray(ring) || ring.length === 0 || ring.some((item) => !Number.isInteger(item))) {
        throw new Error(`${field}[${polygonIndex}][${ringIndex}] must contain integer arc indexes`);
      }
    }
  }
}

function numericPair(value: unknown, field: string): [number, number] {
  if (!Array.isArray(value) || value.length !== 2) throw new Error(`${field} must be a numeric pair`);
  const left = value[0];
  const right = value[1];
  if (typeof left !== "number" || !Number.isFinite(left) || typeof right !== "number" || !Number.isFinite(right)) {
    throw new Error(`${field} must contain finite numbers`);
  }
  return [left, right];
}

function object(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${field} must be an object`);
  }
  return value as Record<string, unknown>;
}

function nonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be a non-empty string`);
  return value;
}

function coordinate(value: number): string {
  return value.toFixed(2);
}

function formatNumber(value: number): string {
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
