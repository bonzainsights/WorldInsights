export interface CountryScopeItem {
  geographyId: number;
  name: string;
  canonicalCode: string;
  checked: boolean;
}

export interface CountryScopeSummary {
  totalCount: number;
  visibleCount: number;
  selectedCount: number;
  visibleSelectedCount: number;
  visibleGeographyIds: number[];
}

export function normalizeCountrySearch(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "")
    .trim()
    .toLocaleLowerCase("en");
}

export function countryMatchesSearch(
  name: string,
  canonicalCode: string,
  query: string,
): boolean {
  const normalizedQuery = normalizeCountrySearch(query);
  if (!normalizedQuery) return true;
  return normalizeCountrySearch(`${name} ${canonicalCode}`).includes(normalizedQuery);
}

export function countryScopeSummary(
  items: readonly CountryScopeItem[],
  query: string,
): CountryScopeSummary {
  const visibleGeographyIds: number[] = [];
  let selectedCount = 0;
  let visibleSelectedCount = 0;

  for (const item of items) {
    if (item.checked) selectedCount += 1;
    if (!countryMatchesSearch(item.name, item.canonicalCode, query)) continue;
    visibleGeographyIds.push(item.geographyId);
    if (item.checked) visibleSelectedCount += 1;
  }

  return {
    totalCount: items.length,
    visibleCount: visibleGeographyIds.length,
    selectedCount,
    visibleSelectedCount,
    visibleGeographyIds,
  };
}

export function wireCountryScopeControls(
  root: HTMLElement,
  onSelectionChange: () => void,
): void {
  const searchInput = root.querySelector<HTMLInputElement>("#country-search");
  if (!searchInput) return;

  const selectVisible = requiredElement<HTMLButtonElement>(root, "#select-visible-countries");
  const clearVisible = requiredElement<HTMLButtonElement>(root, "#clear-visible-countries");
  const countStatus = requiredElement<HTMLElement>(root, "#country-selection-count");
  const emptyStatus = requiredElement<HTMLElement>(root, "#country-search-empty");
  const options = [...root.querySelectorAll<HTMLLabelElement>("[data-country-option]")].map(
    (label) => {
      const input = requiredElement<HTMLInputElement>(label, 'input[name="scope-geography"]');
      const geographyId = Number(input.value);
      if (!Number.isInteger(geographyId) || geographyId <= 0) {
        throw new Error(`invalid country geography ID: ${input.value}`);
      }
      return {
        label,
        input,
        geographyId,
        name: label.dataset.countryName ?? "",
        canonicalCode: label.dataset.countryCode ?? "",
      };
    },
  );

  const refresh = (): void => {
    const items = options.map((option) => ({
      geographyId: option.geographyId,
      name: option.name,
      canonicalCode: option.canonicalCode,
      checked: option.input.checked,
    }));
    const summary = countryScopeSummary(items, searchInput.value);
    const visibleIds = new Set(summary.visibleGeographyIds);

    for (const option of options) {
      option.label.hidden = !visibleIds.has(option.geographyId);
    }

    countStatus.textContent = `${summary.visibleCount} visible · ${summary.selectedCount} selected of ${summary.totalCount}`;
    emptyStatus.hidden = summary.visibleCount !== 0;
    selectVisible.disabled =
      summary.visibleCount === 0 || summary.visibleSelectedCount === summary.visibleCount;
    clearVisible.disabled = summary.visibleSelectedCount === 0;
  };

  const setVisibleSelection = (checked: boolean): void => {
    let changed = false;
    for (const option of options) {
      if (option.label.hidden || option.input.checked === checked) continue;
      option.input.checked = checked;
      changed = true;
    }
    refresh();
    if (changed) onSelectionChange();
  };

  searchInput.addEventListener("input", refresh);
  selectVisible.addEventListener("click", () => setVisibleSelection(true));
  clearVisible.addEventListener("click", () => setVisibleSelection(false));
  root.addEventListener("change", (event) => {
    const target = event.target;
    if (target instanceof HTMLInputElement && target.name === "scope-geography") refresh();
  });
  refresh();
}

function requiredElement<T extends Element>(root: ParentNode, selector: string): T {
  const element = root.querySelector<T>(selector);
  if (!element) throw new Error(`missing required country scope element: ${selector}`);
  return element;
}
