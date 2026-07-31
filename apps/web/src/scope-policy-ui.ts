import type { Operation } from "../../../packages/contracts/src/index.js";
import {
  evaluateOperationScope,
  MAX_TREND_COUNTRIES,
} from "./scope-policy.js";

export const MAX_LABELED_SCATTER_POINTS = 40;

export function shouldSuppressScatterLabels(
  pointCount: number,
  threshold: number = MAX_LABELED_SCATTER_POINTS,
): boolean {
  if (!Number.isInteger(pointCount) || pointCount < 0) {
    throw new Error("pointCount must be a non-negative integer");
  }
  if (!Number.isInteger(threshold) || threshold < 1) {
    throw new Error("threshold must be a positive integer");
  }
  return pointCount > threshold;
}

export function enhanceScopePolicy(root: HTMLElement): void {
  if (root.querySelector("[data-scope-policy-panel]")) return;
  const scopeGrid = root.querySelector<HTMLElement>(".scope-grid");
  if (!scopeGrid) return;
  const operationSelect = document.querySelector<HTMLSelectElement>("#operation-select");
  const loadButton = document.querySelector<HTMLButtonElement>("#load-observations");
  if (!operationSelect || !loadButton) return;

  const geographyInputs = [
    ...root.querySelectorAll<HTMLInputElement>('input[name="scope-geography"]'),
  ];
  const periodInputs = [
    ...root.querySelectorAll<HTMLInputElement>('input[name="scope-period"]'),
  ];
  if (geographyInputs.length === 0 || periodInputs.length === 0) return;

  const panel = document.createElement("div");
  panel.className = "scope-policy-panel";
  panel.dataset.scopePolicyPanel = "true";
  panel.innerHTML = `
    <div class="scope-policy-copy" role="status" aria-live="polite"></div>
    <div class="scope-policy-actions">
      <button data-limit-trend type="button">Keep first ${MAX_TREND_COUNTRIES} selected</button>
      <button data-latest-period type="button">Use latest period</button>
      <button data-all-periods type="button">Select all periods</button>
    </div>`;
  root.insertBefore(panel, scopeGrid);

  const copy = requiredElement<HTMLElement>(panel, ".scope-policy-copy");
  const limitTrend = requiredElement<HTMLButtonElement>(panel, "[data-limit-trend]");
  const latestPeriod = requiredElement<HTMLButtonElement>(panel, "[data-latest-period]");
  const allPeriods = requiredElement<HTMLButtonElement>(panel, "[data-all-periods]");

  const refresh = (): void => {
    const selectedGeographies = geographyInputs.filter((input) => input.checked);
    const selectedPeriods = periodInputs.filter((input) => input.checked);
    const operation = operationSelect.value as Operation;
    const policy = evaluateOperationScope(
      operation,
      selectedGeographies.length,
      selectedPeriods.length,
    );

    panel.classList.toggle("invalid", !policy.valid);
    panel.classList.toggle("valid", policy.valid);
    copy.replaceChildren();
    const heading = document.createElement("strong");
    heading.textContent = policy.valid
      ? "Scope is suitable for this operation."
      : "Adjust the scope before loading chart data.";
    copy.append(heading);
    const detail = document.createElement("p");
    detail.textContent = policy.valid
      ? `${selectedGeographies.length} countries or regions · ${selectedPeriods.length} periods`
      : policy.messages.join(" ");
    copy.append(detail);

    limitTrend.hidden = !(
      policy.countryLimit !== null && selectedGeographies.length > policy.countryLimit
    );
    latestPeriod.hidden = !(
      policy.requiresSinglePeriod && selectedPeriods.length !== 1
    );
    allPeriods.hidden = !(
      policy.requiresMultiplePeriods && selectedPeriods.length < 2 && periodInputs.length >= 2
    );

    if (!policy.valid) {
      loadButton.dataset.scopePolicyDisabled = "true";
      loadButton.disabled = true;
      return;
    }
    if (loadButton.dataset.scopePolicyDisabled === "true") {
      delete loadButton.dataset.scopePolicyDisabled;
      const badge = document.querySelector<HTMLElement>("#compatibility-badge");
      const compatibilityReady = badge?.classList.contains("valid") === true ||
        badge?.classList.contains("warning") === true;
      if (compatibilityReady) loadButton.disabled = false;
    }
  };

  limitTrend.addEventListener("click", () => {
    const selected = geographyInputs.filter((input) => input.checked);
    dispatchSelectionChange(selected.slice(MAX_TREND_COUNTRIES), false);
  });
  latestPeriod.addEventListener("click", () => {
    const latest = periodInputs.at(-1);
    if (!latest) return;
    let firstChanged: HTMLInputElement | null = null;
    for (const input of periodInputs) {
      const nextChecked = input === latest;
      if (input.checked !== nextChecked) firstChanged ??= input;
      input.checked = nextChecked;
    }
    firstChanged?.dispatchEvent(new Event("change", { bubbles: true }));
  });
  allPeriods.addEventListener("click", () => {
    dispatchSelectionChange(periodInputs.filter((input) => !input.checked), true);
  });
  scopeGrid.addEventListener("change", () => queueMicrotask(refresh));
  refresh();
}

export function enhanceScatterDensity(root: HTMLElement): void {
  const chart = root.querySelector<SVGElement>("svg.scatter-chart");
  if (!chart || chart.dataset.densityChecked === "true") return;
  chart.dataset.densityChecked = "true";
  const pointCount = chart.querySelectorAll(".scatter-point").length;
  if (!shouldSuppressScatterLabels(pointCount)) return;
  chart.classList.add("dense-scatter");
  const note = root.querySelector<HTMLElement>(".scatter-card .chart-note");
  if (note) {
    note.append(
      ` Country text labels are hidden for ${pointCount} points; focus a point for its exact country and values.`,
    );
  }
}

export function startScopePolicyUi(): void {
  const applicationRoot = document.querySelector<HTMLElement>("#app");
  if (!applicationRoot) return;
  waitForRoot(applicationRoot, "#scope-controls", (scopeRoot) => {
    const observer = new MutationObserver(() => enhanceScopePolicy(scopeRoot));
    observer.observe(scopeRoot, { childList: true });
    enhanceScopePolicy(scopeRoot);
  });
  waitForRoot(applicationRoot, "#explorer-results", (resultRoot) => {
    const observer = new MutationObserver(() => enhanceScatterDensity(resultRoot));
    observer.observe(resultRoot, { childList: true });
    enhanceScatterDensity(resultRoot);
  });
}

function dispatchSelectionChange(
  inputs: readonly HTMLInputElement[],
  checked: boolean,
): void {
  const firstChanged = inputs.find((input) => input.checked !== checked);
  for (const input of inputs) input.checked = checked;
  firstChanged?.dispatchEvent(new Event("change", { bubbles: true }));
}

function waitForRoot(
  applicationRoot: HTMLElement,
  selector: string,
  attach: (root: HTMLElement) => void,
): void {
  const existing = applicationRoot.querySelector<HTMLElement>(selector);
  if (existing) {
    attach(existing);
    return;
  }
  const observer = new MutationObserver(() => {
    const root = applicationRoot.querySelector<HTMLElement>(selector);
    if (!root) return;
    observer.disconnect();
    attach(root);
  });
  observer.observe(applicationRoot, { childList: true, subtree: true });
}

function requiredElement<T extends Element>(root: ParentNode, selector: string): T {
  const element = root.querySelector<T>(selector);
  if (!element) throw new Error(`missing required scope policy element: ${selector}`);
  return element;
}

if (typeof document !== "undefined") startScopePolicyUi();
