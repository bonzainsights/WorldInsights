import type {
  CoverageManifestV1,
  ObservationV1,
  Operation,
} from "../../../packages/contracts/src/index.js";
import {
  evaluateCoverageCompatibility,
  operationAcceptsIndicatorCount,
  type CompatibilityResult,
  type ReasonCode,
} from "../../../packages/compatibility/src/index.js";
import {
  loadCatalogCoverage,
  loadCatalogObservations,
  ReleaseLoadError,
  type FetchLike,
  type StaticCatalogRelease,
} from "./data.js";

export interface ExplorerSelection {
  operation: Operation;
  indicator_variant_ids: readonly string[];
}

export interface ExplorerScope {
  geography_ids?: readonly number[];
  periods?: readonly string[];
}

export interface CompatibleObservationSet {
  compatibility: CompatibilityResult;
  observations: ReadonlyMap<string, ObservationV1[]>;
}

export class CatalogExplorer {
  readonly release: StaticCatalogRelease;
  readonly fetcher: FetchLike;
  #selection: ExplorerSelection = { operation: "map", indicator_variant_ids: [] };
  #scope: ExplorerScope = {};
  #coverageCache = new Map<string, Promise<CoverageManifestV1>>();
  #observationCache = new Map<string, Promise<ObservationV1[]>>();

  constructor(release: StaticCatalogRelease, fetcher: FetchLike = globalThis.fetch.bind(globalThis)) {
    this.release = release;
    this.fetcher = fetcher;
  }

  get selection(): ExplorerSelection {
    return {
      operation: this.#selection.operation,
      indicator_variant_ids: [...this.#selection.indicator_variant_ids],
    };
  }

  get scope(): ExplorerScope {
    return {
      ...(this.#scope.geography_ids ? { geography_ids: [...this.#scope.geography_ids] } : {}),
      ...(this.#scope.periods ? { periods: [...this.#scope.periods] } : {}),
    };
  }

  setSelection(operation: Operation, indicatorVariantIds: readonly string[]): void {
    const uniqueIds = [...new Set(indicatorVariantIds)];
    if (uniqueIds.length !== indicatorVariantIds.length) {
      throw new ReleaseLoadError("selected indicator IDs must be unique");
    }
    const knownIds = new Set(
      this.release.catalog.indicators.map((indicator) => indicator.indicator_variant_id),
    );
    const unknown = uniqueIds.find((indicatorId) => !knownIds.has(indicatorId));
    if (unknown) throw new ReleaseLoadError(`catalog does not contain indicator: ${unknown}`);
    this.#selection = { operation, indicator_variant_ids: uniqueIds };
    this.#scope = {};
  }

  setScope(scope: ExplorerScope): void {
    const geographyIds = scope.geography_ids ? [...scope.geography_ids] : undefined;
    const periods = scope.periods ? [...scope.periods] : undefined;
    if (geographyIds) {
      if (geographyIds.length === 0) throw new ReleaseLoadError("scope must include at least one geography");
      if (geographyIds.some((geographyId) => !Number.isInteger(geographyId) || geographyId <= 0)) {
        throw new ReleaseLoadError("scope geography IDs must be positive integers");
      }
      if (new Set(geographyIds).size !== geographyIds.length) {
        throw new ReleaseLoadError("scope geography IDs must be unique");
      }
    }
    if (periods) {
      if (periods.length === 0) throw new ReleaseLoadError("scope must include at least one period");
      if (periods.some((period) => !period.trim())) {
        throw new ReleaseLoadError("scope periods cannot be empty");
      }
      if (new Set(periods).size !== periods.length) {
        throw new ReleaseLoadError("scope periods must be unique");
      }
    }
    this.#scope = {
      ...(geographyIds ? { geography_ids: geographyIds } : {}),
      ...(periods ? { periods } : {}),
    };
  }

  async evaluate(): Promise<CompatibilityResult> {
    const { operation, indicator_variant_ids: indicatorIds } = this.#selection;
    if (!operationAcceptsIndicatorCount(operation, indicatorIds.length)) {
      return invalidSelection(indicatorIds.length === 0 ? "no_indicators" : "operation_arity");
    }
    const coverage = await Promise.all(indicatorIds.map((indicatorId) => this.#coverage(indicatorId)));
    return evaluateCoverageCompatibility(operation, coverage);
  }

  async loadCompatibleObservations(): Promise<CompatibleObservationSet> {
    const compatibility = await this.evaluate();
    if (compatibility.status === "invalid") {
      throw new ReleaseLoadError(
        `selection is incompatible: ${compatibility.blockers.join(", ")}`,
      );
    }
    const selectedGeographies = this.#scope.geography_ids
      ? [...this.#scope.geography_ids]
      : compatibility.geography_ids;
    const selectedPeriods = this.#scope.periods
      ? [...this.#scope.periods]
      : compatibility.periods;
    const compatibleGeographies = new Set(compatibility.geography_ids);
    const compatiblePeriods = new Set(compatibility.periods);
    const unavailableGeography = selectedGeographies.find(
      (geographyId) => !compatibleGeographies.has(geographyId),
    );
    if (unavailableGeography !== undefined) {
      throw new ReleaseLoadError(
        `scope geography is unavailable for this selection: ${unavailableGeography}`,
      );
    }
    const unavailablePeriod = selectedPeriods.find((period) => !compatiblePeriods.has(period));
    if (unavailablePeriod !== undefined) {
      throw new ReleaseLoadError(
        `scope period is unavailable for this selection: ${unavailablePeriod}`,
      );
    }
    const allowedGeographies = new Set(selectedGeographies);
    const allowedPeriods = new Set(selectedPeriods);
    const entries = await Promise.all(
      this.#selection.indicator_variant_ids.map(async (indicatorId) => {
        const observations = await this.#observations(indicatorId);
        return [
          indicatorId,
          observations.filter(
            (observation) =>
              allowedGeographies.has(observation.geography_id) &&
              allowedPeriods.has(observation.period_label),
          ),
        ] as const;
      }),
    );
    return { compatibility, observations: new Map(entries) };
  }

  #coverage(indicatorId: string): Promise<CoverageManifestV1> {
    let pending = this.#coverageCache.get(indicatorId);
    if (!pending) {
      pending = loadCatalogCoverage(this.release, indicatorId, this.fetcher);
      this.#coverageCache.set(indicatorId, pending);
    }
    return pending;
  }

  #observations(indicatorId: string): Promise<ObservationV1[]> {
    let pending = this.#observationCache.get(indicatorId);
    if (!pending) {
      pending = loadCatalogObservations(this.release, indicatorId, this.fetcher);
      this.#observationCache.set(indicatorId, pending);
    }
    return pending;
  }
}

function invalidSelection(reason: ReasonCode): CompatibilityResult {
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
