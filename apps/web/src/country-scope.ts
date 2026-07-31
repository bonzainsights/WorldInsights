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

interface CountryOptionElement {
  label: HTMLLabelElement;
  input: HTMLInputElement;
  geographyId: number;
  name: string;
  canonicalCode: string;
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

export function countrySelectionAfterVisibleAction(
  items: readonly CountryScopeItem[],
  query: string,
  checked: boolean,
): Set<number> {
  return new Set(
    items
      .filter((item) =>
        countryMatchesSearch(item.name, item.canonicalCode, query) ? checked : item.checked,
      )
      .filter((item) => item.checked || countryMatchesSearch(item.name, item.canonicalCode, query))
      .map((item) => item.geographyId),
  );
}

export function enhanceCountryScope(root: HTMLElement): void {
  if (root.querySelector("[data-country-scope-toolbar]")) return;
  const options = countryOptionElements(root);
  if (options.length === 0) return;

  const countryList = options[0]?.label.closest<HTMLElement>(".scope-list");
  if (!countryList) throw new Error("country scope list is missing");
  const fieldset = countryList.closest<HTMLFieldSetElement>("fieldset");
  if (!fieldset) throw new Error("country scope fieldset is missing");

  const toolbar = document.createElement("div");
  toolbar.className = "country-scope-toolbar";
  toolbar.dataset.countryScopeToolbar = "true";
  toolbar.innerHTML = `
    <label class="country-search-label" for="country-search">
      <span>Search countries</span>
      <input id="country-search" type="search" autocomplete="off" placeholder="Country name or M49 code" />
    </label>
    <div class="country-scope-actions">
      <button id="select-visible-countries" class="scope-action-button" type="button">Select all visible</button>
      <button id="clear-visible-countries" class="scope-action-button" type="button">Clear visible</button>
    </div>
    <p id="country-selection-count" class="country-selection-count" role="status" aria-live="polite"></p>
    <p id="country-search-empty" class="field-help" hidden>No countries match this search.</p>`;
  fieldset.insertBefore(toolbar, countryList);
  wireCountryScopeControls(fieldset, toolbar, options);
}

export function startCountryScopeEnhancer(): void {
  const root = document.querySelector<HTMLElement>("#scope-controls");
  if (!root) return;
  const observer = new MutationObserver(() => enhanceCountryScope(root));
  observer.observe(root, { childList: true });
  enhanceCountryScope(root);
}

function wireCountryScopeControls(
  fieldset: HTMLFieldSetElement,
  toolbar: HTMLElement,
  options: readonly CountryOptionElement[],
): void {
  const searchInput = requiredElement<HTMLInputElement>(toolbar, "#country-search");
  const selectVisible = requiredElement<HTMLButtonElement>(toolbar, "#select-visible-countries");
  const clearVisible = requiredElement<HTMLButtonElement>(toolbar, "#clear-visible-countries");
  const countStatus = requiredElement<HTMLElement>(toolbar, "#country-selection-count");
  const emptyStatus = requiredElement<HTMLElement>(toolbar, "#country-search-empty");

  const items = (): CountryScopeItem[] => options.map((option) => ({
    geographyId: option.geographyId,
    name: option.name,
    canonicalCode: option.canonicalCode,
    checked: option.input.checked,
  }));

  const refresh = (): void => {
    const summary = countryScopeSummary(items(), searchInput.value);
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
    const selectedIds = countrySelectionAfterVisibleAction(items(), searchInput.value, checked);
    let firstChanged: HTMLInputElement | null = null;
    for (const option of options) {
      const nextChecked = selectedIds.has(option.geographyId);
      if (option.input.checked !== nextChecked) firstChanged ??= option.input;
      option.input.checked = nextChecked;
    }
    refresh();
    firstChanged?.dispatchEvent(new Event("change", { bubbles: true }));
  };

  searchInput.addEventListener("input", refresh);
  selectVisible.addEventListener("click", () => setVisibleSelection(true));
  clearVisible.addEventListener("click", () => setVisibleSelection(false));
  fieldset.addEventListener("change", (event) => {
    const target = event.target;
    if (target instanceof HTMLInputElement && target.name === "scope-geography") refresh();
  });
  refresh();
}

function countryOptionElements(root: HTMLElement): CountryOptionElement[] {
  return [...root.querySelectorAll<HTMLInputElement>('input[name="scope-geography"]')].map(
    (input) => {
      const label = input.closest<HTMLLabelElement>("label.scope-option");
      if (!label) throw new Error(`country ${input.value} is missing its scope label`);
      const geographyId = Number(input.value);
      if (!Number.isInteger(geographyId) || geographyId <= 0) {
        throw new Error(`invalid country geography ID: ${input.value}`);
      }
      const name = label.textContent?.trim() ?? "";
      if (!name) throw new Error(`country ${input.value} is missing its display name`);
      label.dataset.countryOption = "true";
      label.dataset.countryName = name;
      label.dataset.countryCode = input.value;
      return {
        label,
        input,
        geographyId,
        name,
        canonicalCode: input.value,
      };
    },
  );
}

function requiredElement<T extends Element>(root: ParentNode, selector: string): T {
  const element = root.querySelector<T>(selector);
  if (!element) throw new Error(`missing required country scope element: ${selector}`);
  return element;
}

if (typeof document !== "undefined") startCountryScopeEnhancer();
