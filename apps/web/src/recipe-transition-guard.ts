import type { Operation } from "../../../packages/contracts/src/index.js";
import { operationAcceptsIndicatorCount } from "../../../packages/compatibility/src/index.js";

const TRANSIENT_ARITY_MESSAGE =
  /^operation (map|trend|table|scatter|ratio|correlation) has invalid indicator arity$/;

export function selectionHasValidOperationArity(
  operation: Operation,
  selectedIndicatorCount: number,
): boolean {
  if (!Number.isInteger(selectedIndicatorCount) || selectedIndicatorCount < 0) {
    throw new Error("selectedIndicatorCount must be a non-negative integer");
  }
  return operationAcceptsIndicatorCount(operation, selectedIndicatorCount);
}

export function isTransientRecipeArityError(reason: unknown): boolean {
  return reason instanceof Error && TRANSIENT_ARITY_MESSAGE.test(reason.message);
}

export function startRecipeTransitionGuard(): void {
  const applicationRoot = document.querySelector<HTMLElement>("#app");
  if (!applicationRoot) return;

  applicationRoot.addEventListener(
    "change",
    (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) return;
      if (target.name !== "scope-geography" && target.name !== "scope-period") return;

      const operationSelect = applicationRoot.querySelector<HTMLSelectElement>("#operation-select");
      if (!operationSelect) return;
      const selectedIndicatorCount = applicationRoot.querySelectorAll<HTMLInputElement>(
        'input[name="indicators"]:checked',
      ).length;
      if (
        selectionHasValidOperationArity(
          operationSelect.value as Operation,
          selectedIndicatorCount,
        )
      ) {
        return;
      }

      event.stopImmediatePropagation();
    },
    { capture: true },
  );

  window.addEventListener("unhandledrejection", (event) => {
    if (!isTransientRecipeArityError(event.reason)) return;
    event.preventDefault();
  });
}

if (typeof document !== "undefined") startRecipeTransitionGuard();
