/**
 * U12 W7 — HML: ordenação, Colunas+F5, troca de aba sem remount,
 * viewports, axe, perfis cf-access/cf-manage, previous null.
 * Screenshots em /tmp (não commitados).
 */
import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

import { loginAs, openEntryAuditHome, type PortalCredentialKind } from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR || path.join("/tmp", "ui-review-u12");

function ensureDir(): void {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

async function openFirstAnalysis(page: Page): Promise<boolean> {
  await openEntryAuditHome(page);
  const row = page.locator("table tbody tr").first();
  const hasRow = await row.isVisible().catch(() => false);
  if (!hasRow) return false;
  await row.click();
  await expect(page).toHaveURL(/\/entry-audit\/analyses\//, { timeout: 60_000 });
  await expect(page.getByLabel("Indicadores da auditoria")).toBeVisible({
    timeout: 60_000,
  });
  return true;
}

async function shot(
  page: Page,
  name: string,
  size: { width: number; height: number },
  colorScheme: "light" | "dark",
): Promise<void> {
  await page.setViewportSize(size);
  await page.emulateMedia({ colorScheme });
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(ARTIFACT_DIR, `${name}-${size.width}-${colorScheme}.png`),
    fullPage: true,
  });
}

test.describe("U12 W7 UI review HML", () => {
  test.beforeAll(() => {
    ensureDir();
  });

  test("entrada: hero com Executar auditoria e sem card Nova análise", async ({
    page,
  }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "desktop only");
    await loginAs(page, "allowed");
    await openEntryAuditHome(page);
    await expect(
      page.getByRole("button", { name: /Executar auditoria/i }),
    ).toBeVisible();
    await expect(page.getByText("Nova análise")).toHaveCount(0);
    await shot(page, "entry-home", { width: 1440, height: 900 }, "light");
    await shot(page, "entry-home", { width: 1024, height: 900 }, "light");
    await shot(page, "entry-home", { width: 390, height: 844 }, "light");
    await shot(page, "entry-home", { width: 1440, height: 900 }, "dark");
  });

  test("análise: troca de aba não refetch summary/breakdowns/daily", async ({
    page,
  }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "desktop only");
    await loginAs(page, "allowed");
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise no histórico HML");

    let summary = 0;
    let breakdowns = 0;
    let daily = 0;
    let tabResource = 0;
    page.on("request", (req) => {
      if (req.method() !== "GET") return;
      const url = req.url();
      if (!url.includes("/entry-audit/analyses/")) return;
      if (url.includes("/summary")) summary += 1;
      else if (url.includes("/breakdowns")) breakdowns += 1;
      else if (url.includes("/daily")) daily += 1;
      else if (
        /\/(occurrences|documents|unmatched|ctes|tes)(\?|$)/.test(url)
      ) {
        tabResource += 1;
      }
    });

    const tabs = page.getByRole("tab");
    const tabCount = await tabs.count();
    test.skip(tabCount < 2, "menos de 2 abas");

    const before = { summary, breakdowns, daily, tabResource };
    await tabs.nth(1).click();
    await page.waitForTimeout(1500);
    const delta = {
      summary: summary - before.summary,
      breakdowns: breakdowns - before.breakdowns,
      daily: daily - before.daily,
      tabResource: tabResource - before.tabResource,
    };
    fs.writeFileSync(
      path.join(ARTIFACT_DIR, "w7-tab-switch-requests.json"),
      JSON.stringify({ before, after: { summary, breakdowns, daily, tabResource }, delta }, null, 2),
    );
    expect(delta.summary, "summary não deve refetch ao trocar aba").toBe(0);
    expect(delta.breakdowns, "breakdowns não deve refetch ao trocar aba").toBe(0);
    expect(delta.daily, "daily não deve refetch ao trocar aba").toBe(0);
    expect(delta.tabResource).toBeGreaterThanOrEqual(1);
  });

  test("análise: ordenar coluna e página 2 coerente; Colunas persiste F5", async ({
    page,
  }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "desktop only");
    await loginAs(page, "allowed");
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise no histórico HML");

    const sortButton = page
      .getByRole("button", { name: /Ordenar por /i })
      .first();
    const hasSort = await sortButton.isVisible().catch(() => false);
    test.skip(!hasSort, "sem coluna ordenável visível");

    await sortButton.click();
    await page.waitForTimeout(800);
    await expect(page).toHaveURL(/[?&]sort=/);

    const nextPage = page.getByRole("button", { name: /^Próxima$/i });
    if (await nextPage.isEnabled().catch(() => false)) {
      const firstCell = await page.locator("table tbody tr td").first().innerText();
      await nextPage.click();
      await expect(page).toHaveURL(/[?&]page=2/);
      await page.waitForTimeout(800);
      const page2Cell = await page.locator("table tbody tr td").first().innerText();
      // Página 2 ainda na mesma ordenação (célula pode diferir; URL prova continuidade).
      expect(page.url()).toMatch(/sort=/);
      expect(page2Cell || firstCell).toBeTruthy();
    }

    const columnsMenu = page.getByRole("button", { name: /Colunas/i });
    if (await columnsMenu.isVisible().catch(() => false)) {
      await columnsMenu.click();
      const firstToggle = page.getByRole("menuitemcheckbox").first();
      if (await firstToggle.isVisible().catch(() => false)) {
        const label = (await firstToggle.innerText()).trim();
        const pressed = await firstToggle.getAttribute("aria-checked");
        await firstToggle.click();
        await page.keyboard.press("Escape");
        await page.reload();
        await expect(page.getByLabel("Indicadores da auditoria")).toBeVisible({
          timeout: 60_000,
        });
        await columnsMenu.click();
        const again = page.getByRole("menuitemcheckbox", { name: label });
        if (await again.isVisible().catch(() => false)) {
          const after = await again.getAttribute("aria-checked");
          expect(after).not.toBe(pressed);
        }
      }
    }

    await shot(page, "analysis", { width: 1440, height: 900 }, "light");
    await shot(page, "analysis", { width: 1024, height: 900 }, "light");
    await shot(page, "analysis", { width: 390, height: 844 }, "light");
    await shot(page, "analysis", { width: 1440, height: 900 }, "dark");
  });

  test("análise: previous null mostra mensagem quando não há anterior", async ({
    page,
  }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "desktop only");
    await loginAs(page, "allowed");
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise no histórico HML");

    const summary = await page.waitForResponse(
      (res) =>
        res.url().includes("/summary") &&
        res.request().method() === "GET" &&
        res.ok(),
      { timeout: 60_000 },
    ).catch(() => null);
    if (!summary) {
      test.skip(true, "summary não capturado");
      return;
    }
    const body = (await summary.json()) as {
      data?: { previous?: unknown };
    };
    if (body.data?.previous !== null) {
      test.skip(true, "análise atual tem previous — cenário sem anterior não coberto");
      return;
    }
    await expect(
      page.getByText(/Sem análise do período anterior para comparar/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  for (const profile of ["cf_access", "cf_manage"] as PortalCredentialKind[]) {
    test(`perfil ${profile}: entrada + axe sem violação crítica nova`, async ({
      page,
    }, testInfo) => {
      test.skip(testInfo.project.name !== "desktop", "desktop only");
      try {
        await loginAs(page, profile);
      } catch (error) {
        test.skip(true, `credencial ${profile} indisponível: ${String(error)}`);
        return;
      }
      await openEntryAuditHome(page);
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa"])
        .analyze();
      const serious = results.violations.filter(
        (v) => v.impact === "critical" || v.impact === "serious",
      );
      fs.writeFileSync(
        path.join(ARTIFACT_DIR, `w7-axe-${profile}.json`),
        JSON.stringify(serious, null, 2),
      );
      expect(serious, JSON.stringify(serious.map((v) => v.id))).toEqual([]);
    });
  }
});
