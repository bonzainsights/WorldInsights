import { loadStaticRelease, type StaticRelease } from "./data.js";

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
    renderRelease(root, release);
  } catch (error) {
    renderError(root, error);
  }
}

function renderRelease(root: HTMLElement, release: StaticRelease): void {
  if (release.kind === "catalog") {
    renderCatalog(root, release);
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


function renderCatalog(
  root: HTMLElement,
  release: Extract<StaticRelease, { kind: "catalog" }>,
): void {
  root.innerHTML = `
    <header class="hero">
      <div>
        <p class="eyebrow">Static-first global data explorer</p>
        <h1>WorldInsights</h1>
        <p class="lede">A verified multi-indicator catalog is ready for exploration.</p>
      </div>
      <span class="release-badge">${escapeHtml(release.latest.release_id)}</span>
    </header>
    <main>
      <section class="metrics" aria-label="Catalog summary">
        ${metric("Provider", release.catalog.release.provider_id)}
        ${metric("Indicators", String(release.catalog.indicators.length))}
        ${metric("Dataset", release.catalog.release.dataset_id)}
        ${metric("Pipeline", release.catalog.release.pipeline_version)}
      </section>
      <section class="panel">
        <p class="eyebrow">Available indicators</p>
        <div class="bars" role="list">
          ${release.catalog.indicators.map((indicator) => `
            <article class="bar-row" role="listitem">
              <div class="bar-label">
                <strong>${escapeHtml(indicator.name)}</strong>
                <span>${indicator.row_count} rows</span>
              </div>
              <small>${escapeHtml(indicator.provider_id)} · ${escapeHtml(indicator.unit_id)} · ${escapeHtml(indicator.frequency)}</small>
            </article>`).join("")}
        </div>
      </section>
    </main>`;
}

function renderError(root: HTMLElement, error: unknown): void {
  const message = error instanceof Error ? error.message : String(error);
  root.innerHTML = `
    <main class="error-panel">
      <p class="eyebrow">Release validation failed</p>
      <h1>WorldInsights could not load this release.</h1>
      <p>${escapeHtml(message)}</p>
    </main>`;
}

function metric(label: string, value: string): string {
  return `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function formatNumber(value: number | null): string {
  return value === null ? "No data" : new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
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
