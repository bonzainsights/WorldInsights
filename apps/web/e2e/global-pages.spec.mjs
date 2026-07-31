import { readFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

async function waitForScope(page) {
  await expect(page.locator("#scope-controls .scope-grid")).toBeVisible();
  await expect(page.locator("[data-scope-policy-panel]")).toBeVisible();
  await expect(page.locator("#compatibility-badge")).not.toHaveText(/checking/i);
}

test("global selection, chart policies, pagination, and CSV work together", async ({ page }) => {
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.goto("./", { waitUntil: "domcontentloaded" });
  await expect(page.locator("#operation-select")).toBeVisible();
  await expect(page.locator("#country-search")).toBeVisible();

  const countryInputs = page.locator('input[name="scope-geography"]');
  const countryCount = await countryInputs.count();
  expect(countryCount).toBeGreaterThanOrEqual(200);
  await expect(page.locator("#country-selection-count")).toContainText(
    `${countryCount} visible · ${countryCount} selected`,
  );

  const countrySearch = page.locator("#country-search");
  await countrySearch.fill("Nepal");
  await expect(page.locator("[data-country-option]:not([hidden])")).toHaveCount(1);
  await expect(page.locator("#country-selection-count")).toContainText("1 visible");

  await page.getByRole("button", { name: "Clear visible" }).click();
  await expect.poll(
    () => page.locator('input[name="scope-geography"]:checked').count(),
  ).toBe(countryCount - 1);
  await page.getByRole("button", { name: "Select all visible" }).click();
  await expect.poll(
    () => page.locator('input[name="scope-geography"]:checked').count(),
  ).toBe(countryCount);
  await countrySearch.fill("");

  const operation = page.locator("#operation-select");
  const indicators = page.locator('input[name="indicators"]');
  const gdp = page.locator('input[name="indicators"][value="wb.ny.gdp.pcap.cd"]');
  const lifeExpectancy = page.locator(
    'input[name="indicators"][value="wb.sp.dyn.le00.in"]',
  );
  await expect(indicators).toHaveCount(3);
  await expect(gdp).toBeChecked();
  await expect(lifeExpectancy).not.toBeChecked();

  await operation.selectOption("scatter");
  await lifeExpectancy.check();
  await waitForScope(page);

  const loadButton = page.locator("#load-observations");
  await expect(page.getByRole("button", { name: "Use latest period" })).toBeVisible();
  await expect(loadButton).toBeDisabled();
  await page.getByRole("button", { name: "Use latest period" }).click();
  await expect.poll(
    () => page.locator('input[name="scope-period"]:checked').count(),
  ).toBe(1);

  const period2023 = page.locator('input[name="scope-period"][value="2023"]');
  await expect(period2023).toBeVisible();
  if (!(await period2023.isChecked())) {
    const selectedPeriod = page.locator('input[name="scope-period"]:checked');
    const selectedValue = await selectedPeriod.inputValue();
    await period2023.check();
    await page.locator(`input[name="scope-period"][value="${selectedValue}"]`).uncheck();
  }
  await expect.poll(
    () => page.locator('input[name="scope-period"]:checked').count(),
  ).toBe(1);
  await expect(period2023).toBeChecked();
  await expect(loadButton).toBeEnabled();
  await expect.poll(() => new URL(page.url()).searchParams.has("r")).toBe(true);

  await loadButton.click();
  const scatter = page.locator("svg.scatter-chart");
  await expect(scatter).toBeVisible({ timeout: 30_000 });
  const pointCount = await scatter.locator(".scatter-point").count();
  expect(pointCount).toBeGreaterThan(40);
  await expect(scatter).toHaveClass(/dense-scatter/);

  const observationTable = page.locator("table.data-table").first();
  const resultRowCount = await observationTable.locator("tbody tr").count();
  expect(resultRowCount).toBeGreaterThan(100);
  await expect(page.locator(".result-pagination-status")).toHaveText(
    `Showing 100 of ${resultRowCount} rows`,
  );
  await expect(observationTable.locator("tbody tr:visible")).toHaveCount(100);

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV" }).click();
  const download = await downloadPromise;
  const downloadPath = await download.path();
  expect(downloadPath).not.toBeNull();
  const csv = await readFile(downloadPath, "utf8");
  expect(csv.trimEnd().split(/\r?\n/)).toHaveLength(resultRowCount + 1);

  await page.getByRole("button", { name: `Show all ${resultRowCount} rows` }).click();
  await expect(observationTable.locator("tbody tr:visible")).toHaveCount(resultRowCount);

  await operation.selectOption("trend");
  await lifeExpectancy.uncheck();
  await waitForScope(page);
  await expect(page.getByRole("button", { name: "Keep first 5 selected" })).toBeVisible();
  await expect(loadButton).toBeDisabled();
  await page.getByRole("button", { name: "Keep first 5 selected" }).click();
  await expect.poll(
    () => page.locator('input[name="scope-geography"]:checked').count(),
  ).toBe(5);
  await expect(loadButton).toBeEnabled();

  await loadButton.click();
  await expect(page.locator("svg.trend-chart")).toBeVisible({ timeout: 30_000 });
  await expect(page.locator(".chart-legend li")).toHaveCount(5);
  await expect(page.locator(".result-pagination")).toHaveCount(0);
  expect(pageErrors).toEqual([]);
});
