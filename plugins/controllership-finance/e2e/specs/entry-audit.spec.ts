import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { loginAs, openEntryAuditHome, waitForSummaryKpis } from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR ||
  path.join("/tmp", "entry-audit-t12-artifacts");

function ensureArtifactDir(): void {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

test.describe("Auditoria de Entradas — HML", () => {
  test("autorizado: home → análise → filtros → ocorrência → export", async ({
    page,
  }, testInfo) => {
    ensureArtifactDir();
    await loginAs(page, "allowed");
    await openEntryAuditHome(page);
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, `home-${testInfo.project.name}.png`),
      fullPage: true,
    });

    const historyRow = page.locator("table tbody tr").first();
    await expect(historyRow).toBeVisible({ timeout: 30_000 });
    const summaryPromise = waitForSummaryKpis(page);
    await historyRow.click();

    await expect(
      page.getByRole("heading", { name: /Análise de |Resultado da análise/i }),
    ).toBeVisible({ timeout: 45_000 });

    const analysisMatch = page.url().match(/\/analyses\/([^/?#]+)/);
    expect(analysisMatch?.[1]).toBeTruthy();

    const apiKpis = await summaryPromise;
    const kpiStrip = page.getByLabel("Indicadores da auditoria");
    await expect(kpiStrip).toBeVisible();
    await expect(kpiStrip).toContainText(String(apiKpis.documents));
    await expect(kpiStrip).toContainText(String(apiKpis.occurrences));
    if (apiKpis.high > 0) {
      await expect(kpiStrip).toContainText(String(apiKpis.high));
    }

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, `analysis-${testInfo.project.name}.png`),
      fullPage: true,
    });

    const highChip = page
      .getByRole("button", { name: /Alta/i })
      .or(page.locator("[aria-label*='severidade'] button").filter({ hasText: /Alta/i }))
      .first();
    if (await highChip.isVisible().catch(() => false)) {
      await highChip.click();
      await expect(page).toHaveURL(/severity=/);
    }

    const occurrenceRow = page.locator("table tbody tr").first();
    if (await occurrenceRow.isVisible().catch(() => false)) {
      await occurrenceRow.click();
      await expect(
        page.getByRole("heading", { name: /.+/ }).first(),
      ).toBeVisible({ timeout: 30_000 });
      await page.screenshot({
        path: path.join(
          ARTIFACT_DIR,
          `occurrence-${testInfo.project.name}.png`,
        ),
        fullPage: true,
      });

      const resolveBtn = page.getByRole("button", {
        name: /Marcar como resolvida|Resolver/i,
      });
      const reopenBtn = page.getByRole("button", { name: /Reabrir/i });
      if (await resolveBtn.isVisible().catch(() => false)) {
        await resolveBtn.click();
        await expect(reopenBtn).toBeVisible({ timeout: 20_000 });
        await reopenBtn.click();
        await expect(resolveBtn).toBeVisible({ timeout: 20_000 });
      } else if (await reopenBtn.isVisible().catch(() => false)) {
        await reopenBtn.click();
        await expect(resolveBtn).toBeVisible({ timeout: 20_000 });
        await resolveBtn.click();
        await expect(reopenBtn).toBeVisible({ timeout: 20_000 });
      }

      await page.getByRole("button", { name: /Voltar para a análise/i }).click();
    }

    const exportBtn = page.getByRole("button", { name: /Exportar XLSX/i });
    await expect(exportBtn).toBeVisible();
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 60_000 }),
      exportBtn.click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/auditoria-entradas/i);
  });

  test("sem access: estado de sem acesso", async ({ page }) => {
    await loginAs(page, "denied");
    await page.goto("/apps/controllership-finance/entry-audit");
    await expect(
      page
        .getByText(
          /não tem autorização|Aplicação indisponível|não está disponível na sua conta|sem acesso|forbidden/i,
        )
        .first(),
    ).toBeVisible({ timeout: 45_000 });
  });
});
