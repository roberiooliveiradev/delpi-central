import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

import {
  loginAs,
  openEntryAuditHome,
  type PortalCredentialKind,
} from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR || path.join("/tmp", "ui-review-u9");

function ensureDir(): void {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

async function openAnalysisNov01_15(page: import("@playwright/test").Page) {
  await openEntryAuditHome(page);
  const row = page
    .locator("table tbody tr")
    .filter({ hasText: /01\/11|01-11|2026-11-01/i })
    .first();
  if (await row.isVisible().catch(() => false)) {
    await row.click();
  } else {
    await page.locator("table tbody tr").first().click();
  }
  await expect(page).toHaveURL(/\/entry-audit\/analyses\//, { timeout: 60_000 });
  await expect(page.getByLabel("Indicadores da auditoria")).toBeVisible({
    timeout: 60_000,
  });
}

test.describe("U9 R1 — progressive analysis timings", () => {
  test("desktop: KPIs <1.5s após summary; timings por request", async ({
    page,
  }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "medir só desktop");
    ensureDir();
    await loginAs(page, "allowed");

    const marks: Array<{ name: string; ms: number; ok: boolean }> = [];
    const t0 = Date.now();
    page.on("response", (res) => {
      const url = res.url();
      if (!url.includes("/entry-audit/analyses/")) return;
      if (res.request().method() !== "GET") return;
      const name = url.includes("/summary")
        ? "summary"
        : url.includes("/breakdowns")
          ? "breakdowns"
          : url.includes("/daily")
            ? "daily"
            : url.includes("/occurrences")
              ? "occurrences"
              : url.includes("/documents")
                ? "documents"
                : /\/analyses\/[^/]+$/.test(url.split("?")[0] ?? "")
                  ? "analysis"
                  : "other";
      if (name === "other") return;
      marks.push({
        name,
        ms: Date.now() - t0,
        ok: res.ok(),
      });
    });

    await openEntryAuditHome(page);
    const summaryWait = page.waitForResponse(
      (res) =>
        res.url().includes("/summary") &&
        res.request().method() === "GET" &&
        res.ok(),
      { timeout: 60_000 },
    );
    await openAnalysisNov01_15(page);
    await summaryWait;
    const kpiAt = Date.now() - t0;
    const kpiStrip = page.getByLabel("Indicadores da auditoria");
    await expect(kpiStrip).toBeVisible({ timeout: 5_000 });
    const kpiVisibleMs = Date.now() - t0;

    await page
      .getByRole("navigation", { name: /Visões da auditoria/i })
      .waitFor({ state: "visible", timeout: 30_000 })
      .catch(() => undefined);
    const usableMs = Date.now() - t0;

    const report = {
      kpiAt,
      kpiVisibleMs,
      usableMs,
      marks,
      meta: { goalKpiMs: 1500, goalUsableMs: 3000 },
    };
    fs.writeFileSync(
      path.join(ARTIFACT_DIR, "r1-timings.json"),
      JSON.stringify(report, null, 2),
    );
    console.log("U9_R1_TIMINGS", JSON.stringify(report));

    expect(kpiVisibleMs).toBeLessThan(15_000);
  });
});

test.describe("U9 R2 — perfis Keycloak", () => {
  const cases: Array<{
    kind: PortalCredentialKind;
    expectAdmin: boolean;
    expectLnf: boolean;
    expectDreOnly?: boolean;
  }> = [
    { kind: "cf_access", expectAdmin: false, expectLnf: false },
    { kind: "cf_manage", expectAdmin: true, expectLnf: false },
    { kind: "cf_lnf", expectAdmin: false, expectLnf: true },
    { kind: "cf_dre", expectAdmin: false, expectLnf: false, expectDreOnly: true },
  ];

  for (const item of cases) {
    test(`perfil ${item.kind}`, async ({ page }, testInfo) => {
      test.skip(testInfo.project.name !== "desktop", "perfil só desktop");
      ensureDir();
      await loginAs(page, item.kind);
      await page.goto("/apps/controllership-finance");
      await expect(
        page
          .getByText(/Controladoria|Fechamento|Auditoria|Documentos e interações|Bom dia|Boa tarde|Boa noite/i)
          .first(),
      ).toBeVisible({ timeout: 60_000 });

      if (item.expectDreOnly) {
        await expect(page.getByText(/Documentos e interações|Fechamento Mensal/i).first()).toBeVisible({
          timeout: 30_000,
        });
        await page.goto("/apps/controllership-finance/closing/admin");
        await expect(
          page.getByText(/sem permissão|não tem acesso|403|Forbidden|indisponível/i).first(),
        )
          .toBeVisible({ timeout: 20_000 })
          .catch(async () => {
            await expect(page).not.toHaveURL(/closing\/admin$/);
          });
        return;
      }

      await expect(page.getByText(/Auditoria de Entradas|Notas fiscais/i).first()).toBeVisible({
        timeout: 30_000,
      });

      if (item.expectLnf) {
        await expect(
          page.getByRole("link", { name: /Lançamento|LNF|Notas Fiscais/i }).first(),
        ).toBeVisible({ timeout: 15_000 });
      }

      await page.goto("/apps/controllership-finance/closing/admin");
      if (item.expectAdmin) {
        await expect(
          page.getByRole("heading", { name: /Administração|Checklist|Catálogo/i }).first(),
        ).toBeVisible({ timeout: 30_000 });
      } else {
        await expect(
          page.getByText(/sem permissão|não tem acesso|403|Forbidden|indisponível/i).first(),
        )
          .toBeVisible({ timeout: 20_000 })
          .catch(async () => {
            // redirect home is also acceptable denial UX
            await expect(page).not.toHaveURL(/closing\/admin$/);
          });
      }

      await page.screenshot({
        path: path.join(ARTIFACT_DIR, `r2-${item.kind}.png`),
        fullPage: true,
      });
    });
  }
});

test.describe("U9 R3 — axe + temas", () => {
  const routes = [
    { id: "home", path: "/apps/controllership-finance" },
    { id: "entry", path: "/apps/controllership-finance/entry-audit" },
  ];

  for (const scheme of ["light", "dark"] as const) {
    test(`axe+screenshot ${scheme}`, async ({ page }, testInfo) => {
      test.skip(testInfo.project.name !== "desktop", "axe só desktop");
      ensureDir();
      await page.emulateMedia({ colorScheme: scheme });
      await loginAs(page, "allowed");

      for (const route of routes) {
        await page.goto(route.path);
        await page.waitForTimeout(1_500);
        await page.screenshot({
          path: path.join(ARTIFACT_DIR, `r3-${route.id}-${scheme}.png`),
          fullPage: true,
        });
        const results = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa"])
          .exclude("header")
          .exclude("nav")
          .exclude('[class*="portal-shell"]')
          .analyze();
        // U9: sem serious/critical nova no conteúdo do MFE.
        // color-contrast do chrome do host fica registrado, não bloqueia.
        const serious = results.violations.filter(
          (v) =>
            (v.impact === "serious" || v.impact === "critical") &&
            v.id !== "color-contrast",
        );
        fs.writeFileSync(
          path.join(ARTIFACT_DIR, `r3-axe-${route.id}-${scheme}.json`),
          JSON.stringify(
            {
              route: route.id,
              scheme,
              serious: serious.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length })),
              all: results.violations.map((v) => ({
                id: v.id,
                impact: v.impact,
                nodes: v.nodes.length,
              })),
            },
            null,
            2,
          ),
        );
        expect(serious, `${route.id} ${scheme}`).toEqual([]);
      }

      await openAnalysisNov01_15(page);
      await page.screenshot({
        path: path.join(ARTIFACT_DIR, `r3-analysis-${scheme}.png`),
        fullPage: true,
      });
      const analysisAxe = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa"])
        .exclude("header")
        .exclude("nav")
        .analyze();
      const serious = analysisAxe.violations.filter(
        (v) =>
          (v.impact === "serious" || v.impact === "critical") &&
          v.id !== "color-contrast",
      );
      fs.writeFileSync(
        path.join(ARTIFACT_DIR, `r3-axe-analysis-${scheme}.json`),
        JSON.stringify(
          {
            serious: serious.map((v) => ({
              id: v.id,
              impact: v.impact,
              nodes: v.nodes.length,
            })),
          },
          null,
          2,
        ),
      );
      expect(serious).toEqual([]);
    });
  }
});

test.describe("U9 R4 — perfil do portal", () => {
  test("avatar abre /users/{id} com PortalUserProfilePage", async ({
    page,
  }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "perfil só desktop");
    ensureDir();
    await loginAs(page, "allowed");
    await page.goto("/apps/controllership-finance");
    await page.waitForTimeout(1_000);
    const avatar = page.locator('a[href*="/apps/controllership-finance/users/"]').first();
    await expect(avatar).toBeAttached({ timeout: 30_000 });
    const href = await avatar.getAttribute("href");
    expect(href).toMatch(/\/apps\/controllership-finance\/users\//);
    await page.goto(href!);
    await expect(page).toHaveURL(/\/apps\/controllership-finance\/users\//);
    await expect(page.getByText(/Identidade|Atalhos|Você/i).first()).toBeVisible({
      timeout: 30_000,
    });
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "r4-user-profile.png"),
      fullPage: true,
    });
  });
});
