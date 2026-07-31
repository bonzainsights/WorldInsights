import type { Operation } from "../../../packages/contracts/src/index.js";
import { loadWorldTopology } from "./choropleth.js";
import { choroplethMapHtmlM49 } from "./choropleth-m49.js";
import { loadStaticRelease } from "./data.js";
import { CatalogExplorer } from "./explorer.js";

let enhancing = false;

async function enhanceLoadedMap(): Promise<void> {
  if (enhancing) return;
  const results = document.querySelector<HTMLElement>("#explorer-results");
  const operation = document.querySelector<HTMLSelectElement>("#operation-select");
  if (!results || !operation) return;

  deduplicateExportButtons(results);
  if (operation.value !== "map" || !results.querySelector(".data-table")) return;
  if (results.querySelector("[data-worldinsights-map]")) return;

  const container = document.createElement("section");
  container.dataset.worldinsightsMap = "loading";
  container.innerHTML = "<p>Loading version-pinned country geometry…</p>";
  results.prepend(container);
  enhancing = true;
  try {
    const release = await loadStaticRelease();
    if (release.kind !== "catalog") throw new Error("choropleth requires a catalog release");
    const indicatorIds = [
      ...document.querySelectorAll<HTMLInputElement>('input[name="indicators"]:checked'),
    ].map((input) => input.value);
    const geographyIds = [
      ...document.querySelectorAll<HTMLInputElement>('input[name="scope-geography"]:checked'),
    ].map((input) => Number(input.value));
    const periods = [
      ...document.querySelectorAll<HTMLInputElement>('input[name="scope-period"]:checked'),
    ].map((input) => input.value);

    const explorer = new CatalogExplorer(release);
    explorer.setSelection(operation.value as Operation, indicatorIds);
    explorer.setScope({ geography_ids: geographyIds, periods });
    const [observationSet, topology] = await Promise.all([
      explorer.loadCompatibleObservations(),
      loadWorldTopology(),
    ]);
    container.dataset.worldinsightsMap = "ready";
    container.innerHTML = choroplethMapHtmlM49(
      release.catalog.indicators,
      release.catalog.geographies,
      observationSet.observations,
      topology,
    );
  } catch (error) {
    container.dataset.worldinsightsMap = "error";
    container.innerHTML = `<p class="inline-error">Map unavailable: ${escapeHtml(errorMessage(error))}. The verified table remains available below.</p>`;
  } finally {
    enhancing = false;
  }
}

function deduplicateExportButtons(results: HTMLElement): void {
  const buttons = [...results.querySelectorAll<HTMLElement>("#export-csv")];
  for (const button of buttons.slice(0, -1)) button.remove();
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
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

const observer = new MutationObserver(() => {
  void enhanceLoadedMap();
});
observer.observe(document.documentElement, { childList: true, subtree: true });
void enhanceLoadedMap();
