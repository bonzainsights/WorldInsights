export const DEFAULT_RESULT_PAGE_SIZE = 100;

export interface ResultTablePageState {
  totalRows: number;
  visibleRows: number;
  remainingRows: number;
  complete: boolean;
}

export function resultTablePageState(
  totalRows: number,
  requestedVisibleRows: number,
): ResultTablePageState {
  if (!Number.isInteger(totalRows) || totalRows < 0) {
    throw new Error("totalRows must be a non-negative integer");
  }
  if (!Number.isInteger(requestedVisibleRows) || requestedVisibleRows < 0) {
    throw new Error("requestedVisibleRows must be a non-negative integer");
  }
  const visibleRows = Math.min(totalRows, requestedVisibleRows);
  const remainingRows = totalRows - visibleRows;
  return {
    totalRows,
    visibleRows,
    remainingRows,
    complete: remainingRows === 0,
  };
}

export function nextVisibleRowCount(
  totalRows: number,
  currentVisibleRows: number,
  pageSize: number = DEFAULT_RESULT_PAGE_SIZE,
): number {
  if (!Number.isInteger(pageSize) || pageSize <= 0) {
    throw new Error("pageSize must be a positive integer");
  }
  const state = resultTablePageState(totalRows, currentVisibleRows);
  return Math.min(totalRows, state.visibleRows + pageSize);
}

export function enhanceResultTable(root: HTMLElement): void {
  const table = root.querySelector<HTMLTableElement>("table.data-table");
  if (!table || table.dataset.resultPagination === "true") return;
  const body = table.tBodies.item(0);
  if (!body) throw new Error("result table is missing its body");
  const rows = [...body.rows];
  if (rows.length <= DEFAULT_RESULT_PAGE_SIZE) return;

  table.dataset.resultPagination = "true";
  const controls = document.createElement("div");
  controls.className = "result-pagination";
  controls.dataset.resultPaginationControls = "true";
  controls.innerHTML = `
    <p class="result-pagination-status" role="status" aria-live="polite"></p>
    <div class="result-pagination-actions">
      <button class="result-pagination-button" data-show-more type="button">Show next ${DEFAULT_RESULT_PAGE_SIZE}</button>
      <button class="result-pagination-button" data-show-all type="button">Show all rows</button>
    </div>`;

  const container = table.closest<HTMLElement>(".table-scroll") ?? table;
  container.insertAdjacentElement("afterend", controls);
  const status = requiredElement<HTMLElement>(controls, ".result-pagination-status");
  const showMore = requiredElement<HTMLButtonElement>(controls, "[data-show-more]");
  const showAll = requiredElement<HTMLButtonElement>(controls, "[data-show-all]");
  let visibleRows = DEFAULT_RESULT_PAGE_SIZE;

  const refresh = (): void => {
    const state = resultTablePageState(rows.length, visibleRows);
    rows.forEach((row, index) => {
      row.hidden = index >= state.visibleRows;
    });
    status.textContent = `Showing ${state.visibleRows} of ${state.totalRows} rows`;
    showMore.hidden = state.complete;
    showAll.hidden = state.complete;
    if (!state.complete) {
      showMore.textContent = `Show next ${Math.min(DEFAULT_RESULT_PAGE_SIZE, state.remainingRows)}`;
      showAll.textContent = `Show all ${state.totalRows} rows`;
    }
  };

  showMore.addEventListener("click", () => {
    visibleRows = nextVisibleRowCount(rows.length, visibleRows);
    refresh();
  });
  showAll.addEventListener("click", () => {
    visibleRows = rows.length;
    refresh();
  });
  refresh();
}

export function startResultTableEnhancer(): void {
  const applicationRoot = document.querySelector<HTMLElement>("#app");
  if (!applicationRoot) return;

  const attach = (): boolean => {
    const resultRoot = applicationRoot.querySelector<HTMLElement>("#explorer-results");
    if (!resultRoot) return false;
    const observer = new MutationObserver(() => enhanceResultTable(resultRoot));
    observer.observe(resultRoot, { childList: true });
    enhanceResultTable(resultRoot);
    return true;
  };

  if (attach()) return;
  const applicationObserver = new MutationObserver(() => {
    if (!attach()) return;
    applicationObserver.disconnect();
  });
  applicationObserver.observe(applicationRoot, { childList: true, subtree: true });
}

function requiredElement<T extends Element>(root: ParentNode, selector: string): T {
  const element = root.querySelector<T>(selector);
  if (!element) throw new Error(`missing required result pagination element: ${selector}`);
  return element;
}

if (typeof document !== "undefined") startResultTableEnhancer();
