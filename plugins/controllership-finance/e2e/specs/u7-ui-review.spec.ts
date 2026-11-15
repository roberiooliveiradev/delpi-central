/**
 * U7 — HML: Início + Auditoria (entrada/análise) em 1440/1024/390.
 * Screenshots em /tmp/ui-review-u7 (não commitados).
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";

import { loginAs, openEntryAuditHome, waitForSummaryKpis } from "../helpers";

const OUT = process.env.CF_E2E_ARTIFACT_DIR || "/tmp/ui-review-u7";
const HOME = "/apps/controllership-finance";

async function shot(page: Page, name: string) {
  fs.mkdirSync(OUT, { recursive: true });
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
}

async function openHome(page: Page) {
  await page.goto(HOME);
  await expect(page.getByText("Caminhos e funcionalidades")).toBeVisible({
    timeout: 45_000,
  });
}

test.describe("U7 UI review HML", () => {
  test("home + entry + analysis @desktop viewports", async ({ page }, info) => {
    test.skip(info.project.name !== "desktop", "desktop");
    await loginAs(page, "allowed");

    // G9 timing — abertura da análise a partir do histórico
    await openHome(page);
    // Highlights H1: nunca traço estático «—»
    await expect(page.getByText("Competência")).toBeVisible();
    await expect(page.getByText("Atenções")).toBeVisible();
    await expect(
      page.getByText(/Nenhuma competência|Aberta|indisponível/i).first(),
    ).toBeVisible({ timeout: 30_000 });
    await page.setViewportSize({ width: 1440, height: 900 });
    await shot(page, "home-1440");
    await page.setViewportSize({ width: 1024, height: 800 });
    await shot(page, "home-1024");
    await page.setViewportSize({ width: 390, height: 844 });
    await shot(page, "home-390");

    await page.setViewportSize({ width: 1440, height: 900 });
    await openEntryAuditHome(page);
    await expect(
      page.getByRole("button", { name: /Executar auditoria/i }),
    ).toBeVisible();
    await expect(page.getByLabel("Caminho da página")).toBeVisible();
    await shot(page, "entry-1440");
    await page.setViewportSize({ width: 1024, height: 800 });
    await shot(page, "entry-1024");
    await page.setViewportSize({ width: 390, height: 844 });
    await shot(page, "entry-390");

    await page.setViewportSize({ width: 1440, height: 900 });
    const historyRow = page.locator("table tbody tr").first();
    const hasHistory = await historyRow.isVisible().catch(() => false);
    test.skip(!hasHistory, "sem análise no histórico HML");

    const t0 = Date.now();
    const summaryPromise = waitForSummaryKpis(page);
    await historyRow.click();
    await expect(
      page.getByRole("heading", { name: /Análise de /i }),
    ).toBeVisible({ timeout: 60_000 });
    const openMs = Date.now() - t0;
    const kpis = await summaryPromise;
    fs.writeFileSync(
      `${OUT}/g9-open-ms.json`,
      JSON.stringify({ openMs, documents: kpis.documents, high: kpis.high }),
    );

    await expect(page.getByLabel("Indicadores da auditoria")).toBeVisible();
    await expect(page.getByLabel("Caminho da página")).toBeVisible();
    await shot(page, "analysis-1440");
    await page.setViewportSize({ width: 1024, height: 800 });
    await shot(page, "analysis-1024");
    await page.setViewportSize({ width: 390, height: 844 });
    await shot(page, "analysis-390");
  });
});
