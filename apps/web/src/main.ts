import type {
  ExplorationRecipeV1,
  Operation,
} from "../../../packages/contracts/src/index.js";
import {
  catalogExplorerShell,
  compatibilityStatusHtml,
  compatibleObservationHtml,
  scopeControlsHtml,
  statusBadgeClass,
} from "./catalog-ui.js";
import { loadStaticRelease, type StaticRelease } from "./data.js";
import { CatalogExplorer, type ExplorerScope } from "./explorer.js";
import {
  recipeForSelection,
  recipeFromUrl,
  urlWithRecipe,
} from "./recipe-url.js";
import {
  compatibleObservationsCsv,
  csvFileName,
  downloadCsv,
} from "./export-csv.js";

const geographyNames: Record<number, string> = {
  1: "Germany",
  2: "Nepal",
  3: "United States",
};

async function start(): Promise<void> {
  const root = document.querySelector<HTMLElement>("#app");
  if (!root) throw new Error("missing #app root");

  try {
    const release = await loadStaticRelease();
    await renderRelease(root, release);
  } catch (error) {
    renderError(root, error);
  }
}

async function renderRelease(root: HTMLElement, release: StaticRelease): Promise<void> {
  if (release.kind === "catalog") {
    await renderCatalog(root, release);
    return;
  }

  const values = release.observations
    .map((observation) => observation.value)
    .filter((value): value is number => value !== null);
  const maximum = Math.max(...values);

  root.innerHTML = `
    <header class="hero">
      <div>
        <p class="eyebrow">Static-first global data explorer</p>
        <h1>WorldInsights</h1>
        <p class="lede">A verified release loaded entirely from immutable static assets.</p>
      </div>
      <span class="release-badge">${escapeHtml(release.latest.release_id)}</span>
    </header>
    <main>
      <section class="metrics" aria-label="Release summary">
        ${metric("Provider", release.manifest.release.provider_id)}
        ${metric("Indicator", release.manifest.indicator.name)}
        ${metric("Countries", String(release.coverage.geography_ids.length))}
        ${metric("Period", release.coverage.periods.join(", "))}
      </section>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Verified observations</p>
            <h2>${escapeHtml(release.manifest.indicator.name)}</h2>
          </div>
          <p>${escapeHtml(release.manifest.indicator.unit_id)}</p>
        </div>
        <div class="bars" role="list">
          ${release.observations
            .map((observation) => {
              const value = observation.value ?? 0;
              const width = maximum > 0 ? (value / maximum) * 100 : 0;
              return `
                <article class="bar-row" role="listitem">
                  <div class="bar-label">
                    <strong>${escapeHtml(geographyNames[observation.geography_id] ?? `Geography ${observation.geography_id}`)}</strong>
                    <span>${formatNumber(observation.value)}</span>
                  </div>
                  <div class="bar-track" aria-hidden="true">
                    <span style="width: ${width.toFixed(2)}%"></span>
                  </div>
                  ${observation.provider_quality_flags.length > 0 ? `<small>Provider flag: ${escapeHtml(observation.provider_quality_flags.join(", "))}</small>` : ""}
                </article>`;
            })
            .join("")}
        </div>
      </section>
      <section class="provenance panel">
        <p class="eyebrow">Provenance</p>
        <dl>
          <div><dt>Dataset</dt><dd>${escapeHtml(release.manifest.release.dataset_id)}</dd></div>
          <div><dt>Retrieved</dt><dd>${escapeHtml(release.manifest.release.retrieved_at)}</dd></div>
          <div><dt>Rows</dt><dd>${release.manifest.row_count}</dd></div>
          <div><dt>Pipeline</dt><dd>${escapeHtml(release.manifest.release.pipeline_version)}</dd></div>
        </dl>
      </section>
    </main>`;
}

async function renderCatalog(
  root: HTMLElement,
  release: Extract<StaticRelease, { kind: "catalog" }>,
): Promise<void> {
  const initialRecipe = await recipeFromUrl(window.location.href);
  if (initialRecipe && initialRecipe.release_id !== release.latest.release_id) {
    throw new Error(
      `recipe release ${initialRecipe.release_id} does not match loaded release ${release.latest.release_id}`,
    );
  }

  root.innerHTML = catalogExplorerShell(release);
  const explorer = new CatalogExplorer(release);
  const form = requiredElement<HTMLFormElement>(root, "#explorer-form");
  const operationSelect = requiredElement<HTMLSelectElement>(root, "#operation-select");
  const status = requiredElement<HTMLElement>(root, "#compatibility-status");
  const badge = requiredElement<HTMLElement>(root, "#compatibility-badge");
  const loadButton = requiredElement<HTMLButtonElement>(root, "#load-observations");
  const scopeControls = requiredElement<HTMLElement>(root, "#scope-controls");
  const results = requiredElement<HTMLElement>(root, "#explorer-results");
  const shareButton = document.createElement("button");
  shareButton.type = "button";
  shareButton.className = "primary-button";
  shareButton.textContent = "Copy shareable link";
  shareButton.style.background = "#173451";
  shareButton.style.color = "#cbe8ff";
  shareButton.style.marginTop = ".65rem";
  loadButton.insertAdjacentElement("afterend", shareButton);
  let revision = 0;
  let recipeToRestore = initialRecipe;

  const selectedIndicatorIds = (): string[] =>
    [...form.querySelectorAll<HTMLInputElement>('input[name="indicators"]:checked')].map(
      (input) => input.value,
    );

  const currentScope = (): ExplorerScope => {
    const geographyInputs = [
      ...scopeControls.querySelectorAll<HTMLInputElement>('input[name="scope-geography"]'),
    ];
    const periodInputs = [
      ...scopeControls.querySelectorAll<HTMLInputElement>('input[name="scope-period"]'),
    ];
    const checkedGeographies = geographyInputs.filter((input) => input.checked).map((input) => Number(input.value));
    const checkedPeriods = periodInputs.filter((input) => input.checked).map((input) => input.value);
    return {
      ...(geographyInputs.length > 0 && checkedGeographies.length < geographyInputs.length
        ? { geography_ids: checkedGeographies }
        : {}),
      ...(periodInputs.length > 0 && checkedPeriods.length < periodInputs.length
        ? { periods: checkedPeriods }
        : {}),
    };
  };

  const syncRecipeUrl = async (): Promise<string> => {
    const recipe = recipeForSelection(
      release.latest.release_id,
      operationSelect.value as Operation,
      selectedIndicatorIds(),
      currentScope(),
    );
    const nextUrl = await urlWithRecipe(window.location.href, recipe);
    window.history.replaceState(null, "", nextUrl);
    return nextUrl;
  };

  const refreshCompatibility = async (): Promise<void> => {
    const currentRevision = ++revision;
    badge.className = "status-badge checking";
    badge.textContent = "Checking";
    status.innerHTML = "<p>Checking compact coverage metadata…</p>";
    scopeControls.innerHTML = `<p class="field-help">Valid countries and periods will appear here.</p>`;
    loadButton.disabled = true;
    explorer.setSelection(operationSelect.value as Operation, selectedIndicatorIds());
    try {
      const compatibility = await explorer.evaluate();
      if (currentRevision !== revision) return;
      status.innerHTML = compatibilityStatusHtml(compatibility);
      badge.className = statusBadgeClass(compatibility.status);
      badge.textContent = compatibility.status;
      scopeControls.innerHTML = scopeControlsHtml(release, compatibility);
      if (recipeToRestore) {
        restoreRecipeScope(scopeControls, explorer, recipeToRestore);
        recipeToRestore = null;
      }
      loadButton.disabled = compatibility.status === "invalid";
      if (compatibility.status !== "invalid") await syncRecipeUrl();
    } catch (error) {
      if (currentRevision !== revision) return;
      status.innerHTML = `<p class="inline-error">${escapeHtml(errorMessage(error))}</p>`;
      badge.className = "status-badge invalid";
      badge.textContent = "error";
      scopeControls.innerHTML = `<p class="inline-error">Scope controls could not be prepared.</p>`;
    }
  };

  if (initialRecipe) restoreRecipeSelection(form, operationSelect, initialRecipe);

  form.addEventListener("change", () => {
    void refreshCompatibility();
  });
  scopeControls.addEventListener("change", () => {
    try {
      const scope = explicitScope(scopeControls);
      explorer.setScope(scope);
      loadButton.disabled = false;
      void syncRecipeUrl();
    } catch (error) {
      loadButton.disabled = true;
      status.innerHTML = `<p class="inline-error">${escapeHtml(errorMessage(error))}</p>`;
    }
  });
  shareButton.addEventListener("click", () => {
    const originalText = shareButton.textContent;
    shareButton.disabled = true;
    void syncRecipeUrl()
      .then((url) => navigator.clipboard.writeText(url))
      .then(() => {
        shareButton.textContent = "Link copied";
      })
      .catch((error) => {
        shareButton.textContent = "Copy failed";
        status.innerHTML = `<p class="inline-error">${escapeHtml(errorMessage(error))}</p>`;
      })
      .finally(() => {
        window.setTimeout(() => {
          shareButton.textContent = originalText;
          shareButton.disabled = false;
        }, 1400);
      });
  });
  loadButton.addEventListener("click", () => {
    const buttonRevision = revision;
    loadButton.disabled = true;
    loadButton.textContent = "Loading verified observations…";
    results.innerHTML = "<p>Downloading only compatible observation partitions…</p>";
    void explorer
      .loadCompatibleObservations()
      .then((observationSet) => {
        if (buttonRevision !== revision) return;
        results.innerHTML = compatibleObservationHtml(release, observationSet);
        const exportButton = document.createElement("button");
        exportButton.id = "export-csv";
        exportButton.className = "primary-button";
        exportButton.type = "button";
        exportButton.textContent = "Download CSV";
        exportButton.addEventListener("click", () => {
          downloadCsv(
            csvFileName(release),
            compatibleObservationsCsv(release, observationSet),
          );
        });
        results.append(exportButton);
      })
      .catch((error) => {
        if (buttonRevision !== revision) return;
        results.innerHTML = `<p class="inline-error">${escapeHtml(errorMessage(error))}</p>`;
      })
      .finally(() => {
        if (buttonRevision !== revision) return;
        loadButton.textContent = "Load compatible data";
        loadButton.disabled = false;
      });
  });

  await refreshCompatibility();
}

function restoreRecipeSelection(
  form: HTMLFormElement,
  operationSelect: HTMLSelectElement,
  recipe: ExplorationRecipeV1,
): void {
  operationSelect.value = recipe.operation;
  const inputs = [...form.querySelectorAll<HTMLInputElement>('input[name="indicators"]')];
  const requested = new Set(recipe.indicator_variant_ids);
  const available = new Set(inputs.map((input) => input.value));
  const unknown = recipe.indicator_variant_ids.find((indicatorId) => !available.has(indicatorId));
  if (unknown) throw new Error(`recipe indicator is not present in this release: ${unknown}`);
  for (const input of inputs) input.checked = requested.has(input.value);
}

function restoreRecipeScope(
  root: HTMLElement,
  explorer: CatalogExplorer,
  recipe: ExplorationRecipeV1,
): void {
  const geographyInputs = [
    ...root.querySelectorAll<HTMLInputElement>('input[name="scope-geography"]'),
  ];
  const periodInputs = [
    ...root.querySelectorAll<HTMLInputElement>('input[name="scope-period"]'),
  ];
  const targetGeographies = recipe.geography.mode === "include"
    ? recipe.geography.geography_ids
    : geographyInputs.map((input) => Number(input.value));
  const targetPeriods = recipe.time.mode === "include"
    ? recipe.time.periods
    : recipe.time.mode === "latest"
      ? [periodInputs.at(-1)?.value].filter((value): value is string => Boolean(value))
      : periodInputs.map((input) => input.value);
  applyCheckedValues(geographyInputs, targetGeographies.map(String), "geography");
  applyCheckedValues(periodInputs, targetPeriods, "period");
  explorer.setScope({
    ...(recipe.geography.mode === "include" ? { geography_ids: targetGeographies } : {}),
    ...(recipe.time.mode !== "all_compatible" ? { periods: targetPeriods } : {}),
  });
}

function explicitScope(root: HTMLElement): ExplorerScope {
  const geographyIds = [
    ...root.querySelectorAll<HTMLInputElement>('input[name="scope-geography"]:checked'),
  ].map((input) => Number(input.value));
  const periods = [
    ...root.querySelectorAll<HTMLInputElement>('input[name="scope-period"]:checked'),
  ].map((input) => input.value);
  return { geography_ids: geographyIds, periods };
}

function applyCheckedValues(
  inputs: readonly HTMLInputElement[],
  selectedValues: readonly string[],
  field: string,
): void {
  const selected = new Set(selectedValues);
  const available = new Set(inputs.map((input) => input.value));
  const unknown = selectedValues.find((value) => !available.has(value));
  if (unknown) throw new Error(`recipe ${field} is unavailable for this selection: ${unknown}`);
  for (const input of inputs) input.checked = selected.has(input.value);
}

function requiredElement<T extends Element>(root: ParentNode, selector: string): T {
  const element = root.querySelector<T>(selector);
  if (!element) throw new Error(`missing required element: ${selector}`);
  return element;
}

function renderError(root: HTMLElement, error: unknown): void {
  root.innerHTML = `
    <main class="error-panel">
      <p class="eyebrow">Release validation failed</p>
      <h1>WorldInsights could not load this release.</h1>
      <p>${escapeHtml(errorMessage(error))}</p>
    </main>`;
}

function metric(label: string, value: string): string {
  return `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function formatNumber(value: number | null): string {
  return value === null ? "No data" : new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
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

void start();
