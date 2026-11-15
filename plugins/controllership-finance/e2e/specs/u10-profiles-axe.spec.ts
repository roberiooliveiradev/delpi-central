import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

import {
  loginAs,
  type PortalCredentialKind,
} from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR || path.join("/tmp", "ui-review-u10");

function ensureDir(): void {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

test.describe("U10 R2 — perfis Keycloak", () => {
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
      test.setTimeout(180_000);
      ensureDir();
      await loginAs(page, item.kind);
      await page.goto("/apps/controllership-finance");
      await expect(
        page
          .getByText(
            /Controladoria|Fechamento|Auditoria|Documentos e interações|Bom dia|Boa tarde|Boa noite/i,
          )
          .first(),
      ).toBeVisible({ timeout: 60_000 });

      if (item.expectDreOnly) {
        await expect(
          page.getByText(/Documentos e interações|Fechamento Mensal/i).first(),
        ).toBeVisible({ timeout: 30_000 });
        await page.goto("/apps/controllership-finance/closing/admin");
        await expect(page).not.toHaveURL(/closing\/admin$/, {
          timeout: 20_000,
        });
        await page.screenshot({
          path: path.join(ARTIFACT_DIR, `r2-${item.kind}.png`),
          fullPage: true,
        });
        return;
      }

      await expect(
        page.getByText(/Auditoria de Entradas|Notas fiscais/i).first(),
      ).toBeVisible({ timeout: 30_000 });

      // LNF no hub é botão (SectionRouteCard), não <a>.
      const lnfControl = page.getByRole("button", {
        name: /Lançamento de notas fiscais/i,
      });
      if (item.expectLnf) {
        await expect(lnfControl.first()).toBeVisible({ timeout: 15_000 });
      } else if (item.kind === "cf_access") {
        // Sibling negativo: access sem LNF não exibe o atalho externo.
        await expect(lnfControl).toHaveCount(0);
      }

      await page.goto("/apps/controllership-finance/closing/admin");
      if (item.expectAdmin) {
        await expect(
          page
            .getByRole("heading", {
              name: /Administração|Checklist|Catálogo/i,
            })
            .first(),
        ).toBeVisible({ timeout: 30_000 });
      } else {
        await expect(page).not.toHaveURL(/closing\/admin$/, {
          timeout: 20_000,
        });
      }

      await page.screenshot({
        path: path.join(ARTIFACT_DIR, `r2-${item.kind}.png`),
        fullPage: true,
      });
    });
  }
});

test.describe("U10 R3 — axe: listar color-contrast e button-name", () => {
  test("inventário com seletor/página/dono", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "axe só desktop");
    ensureDir();
    await loginAs(page, "allowed");

    const routes = [
      { id: "home", path: "/apps/controllership-finance" },
      { id: "entry", path: "/apps/controllership-finance/entry-audit" },
    ];
    const inventory: Array<{
      page: string;
      rule: string;
      impact: string | null | undefined;
      target: string;
      html: string;
      owner: "mfe" | "host" | "plugin-ui" | "unknown";
    }> = [];

    for (const route of routes) {
      await page.goto(route.path);
      await page.waitForTimeout(1_500);
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa"])
        .analyze();
      for (const violation of results.violations) {
        if (violation.id !== "color-contrast" && violation.id !== "button-name") {
          continue;
        }
        for (const node of violation.nodes) {
          const target = (node.target || []).map(String).join(" ");
          const html = String(node.html || "").slice(0, 240);
          // Precedência: kit (delpi-ui) > host shell > MFE local (só cf-*).
          const blob = `${target} ${html}`;
          let owner: "mfe" | "host" | "plugin-ui" | "unknown" = "unknown";
          if (/delpi-ui/i.test(blob)) {
            owner = "plugin-ui";
          } else if (
            /collapse-btn|\.avatar|sidebar-footer|portal-shell|consent-|TopBar|header|nav|aside/i.test(
              blob,
            )
          ) {
            owner = "host";
          } else if (
            /\bcf-|entry-audit|controllership|dashboard-controllership/i.test(
              blob,
            )
          ) {
            owner = "mfe";
          }
          inventory.push({
            page: route.id,
            rule: violation.id,
            impact: violation.impact,
            target,
            html,
            owner,
          });
        }
      }
      await page.screenshot({
        path: path.join(ARTIFACT_DIR, `r3-${route.id}.png`),
        fullPage: true,
      });
    }

    fs.writeFileSync(
      path.join(ARTIFACT_DIR, "r3-axe-inventory.json"),
      JSON.stringify(inventory, null, 2),
    );
    console.log("U10_R3_INVENTORY", JSON.stringify(inventory, null, 2));

    // Corrigir só MFE nesta etapa.
    const mfeIssues = inventory.filter((item) => item.owner === "mfe");
    expect(
      mfeIssues,
      `violações do MFE a corrigir: ${JSON.stringify(mfeIssues)}`,
    ).toEqual([]);
  });
});
