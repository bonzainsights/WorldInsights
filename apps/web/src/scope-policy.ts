import type { Operation } from "../../../packages/contracts/src/index.js";

export const MAX_TREND_COUNTRIES = 5;

export interface OperationScopePolicy {
  valid: boolean;
  messages: string[];
  countryLimit: number | null;
  requiresSinglePeriod: boolean;
  requiresMultiplePeriods: boolean;
}

export function evaluateOperationScope(
  operation: Operation,
  geographyCount: number,
  periodCount: number,
): OperationScopePolicy {
  validateCount(geographyCount, "geographyCount");
  validateCount(periodCount, "periodCount");

  const messages: string[] = [];
  let countryLimit: number | null = null;
  let requiresSinglePeriod = false;
  let requiresMultiplePeriods = false;

  if (geographyCount === 0) messages.push("Select at least one country or region.");
  if (periodCount === 0) messages.push("Select at least one period.");

  if (operation === "trend") {
    countryLimit = MAX_TREND_COUNTRIES;
    requiresMultiplePeriods = true;
    if (geographyCount > MAX_TREND_COUNTRIES) {
      messages.push(
        `Trend charts support at most ${MAX_TREND_COUNTRIES} countries so lines and legends remain distinguishable.`,
      );
    }
    if (periodCount > 0 && periodCount < 2) {
      messages.push("Trend charts require at least two periods.");
    }
  }

  if (operation === "scatter" || operation === "correlation") {
    requiresSinglePeriod = true;
    if (periodCount !== 1) {
      messages.push("Scatter and correlation charts require exactly one period.");
    }
  }

  return {
    valid: messages.length === 0,
    messages,
    countryLimit,
    requiresSinglePeriod,
    requiresMultiplePeriods,
  };
}

function validateCount(value: number, field: string): void {
  if (!Number.isInteger(value) || value < 0) {
    throw new Error(`${field} must be a non-negative integer`);
  }
}
