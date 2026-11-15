import { expect, test } from "@playwright/test";

import { loginAs } from "../helpers";

/**
 * T13R — smoke HML das páginas que usam os 4 componentes evoluídos do plugin-ui
 * e que existem no compose HML. Screenshots em /tmp (não commitados).
 */

const ARTIFACT =
  process.env.CF_E2E_ARTIFACT_DIR || "/tmp/t13r-consumer-smoke-artifacts";

test.describe("T13R consumidores plugin-ui (HML)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "allowed");
  });

  test("commercial home abre (ScopeChipBar)", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(String(err)));
    await page.goto("/apps/commercial");
    await expect(page.locator("body")).toBeVisible({ timeout: 45_000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: `${ARTIFACT}/commercial-home.png`,
      fullPage: true,
    });
    expect(errors, `pageerrors: ${errors.join(" | ")}`).toEqual([]);
  });

  test("engineering product-registration abre (ScopeChipBar)", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(String(err)));
    await page.goto("/apps/engineering/product-registration");
    await expect(page.locator("body")).toBeVisible({ timeout: 45_000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: `${ARTIFACT}/engineering-prc.png`,
      fullPage: true,
    });
    expect(errors, `pageerrors: ${errors.join(" | ")}`).toEqual([]);
  });

  test("controllership-finance entry-audit abre (ScopeChipBar/Semicircle/HVB)", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(String(err)));
    await page.goto("/apps/controllership-finance/entry-audit");
    await expect(
      page.getByRole("heading", { name: /Auditoria de Entradas/i }).first(),
    ).toBeVisible({ timeout: 45_000 });
    const row = page.locator("table tbody tr").first();
    if (await row.isVisible().catch(() => false)) {
      await row.click();
      await expect(
        page.getByRole("heading", { name: /Resultado da análise/i }),
      ).toBeVisible({ timeout: 45_000 });
      await expect(page.getByLabel("Indicadores da auditoria")).toBeVisible();
    }
    await page.screenshot({
      path: `${ARTIFACT}/cf-entry-audit.png`,
      fullPage: true,
    });
    expect(errors, `pageerrors: ${errors.join(" | ")}`).toEqual([]);
  });
});
