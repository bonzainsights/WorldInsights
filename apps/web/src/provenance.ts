import type { StaticCatalogRelease } from "./data.js";

export function provenanceHtml(
  release: StaticCatalogRelease,
  selectedIndicatorIds: readonly string[],
): string {
  const requested = new Set(selectedIndicatorIds);
  if (requested.size !== selectedIndicatorIds.length) {
    throw new Error("provenance indicator IDs must be unique");
  }

  const indicatorById = new Map(
    release.catalog.indicators.map((indicator) => [indicator.indicator_variant_id, indicator]),
  );
  const indicators = selectedIndicatorIds.map((indicatorId) => {
    const indicator = indicatorById.get(indicatorId);
    if (!indicator) throw new Error(`provenance indicator is not in the catalog: ${indicatorId}`);
    return indicator;
  });

  return `
    <section class="provenance result-provenance" aria-labelledby="result-provenance-heading">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Verified provenance</p>
          <h2 id="result-provenance-heading">Where these values came from</h2>
        </div>
        <span class="step-badge">Immutable release</span>
      </div>
      <dl>
        <div><dt>Release</dt><dd>${escapeHtml(release.catalog.release.release_id)}</dd></div>
        <div><dt>Retrieved</dt><dd>${escapeHtml(release.catalog.release.retrieved_at)}</dd></div>
        <div><dt>Provider</dt><dd>${escapeHtml(release.catalog.release.provider_id)}</dd></div>
        <div><dt>Dataset</dt><dd>${escapeHtml(release.catalog.release.dataset_id)}</dd></div>
        <div><dt>Pipeline</dt><dd>${escapeHtml(release.catalog.release.pipeline_version)}</dd></div>
        <div><dt>Source checksum</dt><dd><code>${escapeHtml(release.catalog.release.source_checksum)}</code></dd></div>
      </dl>
      <div class="table-scroll">
        <table class="data-table provenance-table">
          <thead>
            <tr>
              <th scope="col">Feature</th>
              <th scope="col">Provider code</th>
              <th scope="col">Concept</th>
              <th scope="col">Unit</th>
              <th scope="col">Frequency</th>
              <th scope="col">Release rows</th>
            </tr>
          </thead>
          <tbody>
            ${indicators.map((indicator) => `
              <tr>
                <th scope="row">${escapeHtml(indicator.name)}<small>${escapeHtml(indicator.indicator_variant_id)}</small></th>
                <td><code>${escapeHtml(indicator.provider_indicator_code)}</code></td>
                <td>${escapeHtml(indicator.concept_id)}</td>
                <td>${escapeHtml(indicator.unit_id)}</td>
                <td>${escapeHtml(indicator.frequency)}</td>
                <td>${indicator.row_count}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
    </section>`;
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
