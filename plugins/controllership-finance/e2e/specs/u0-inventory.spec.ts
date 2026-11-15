/**
 * U0 — inventário visual (screenshots). Não valida aceite de produto.
 * Artefatos em /tmp/ui-review-u0 (não commitados).
 */
import { expect, test, type Page } from "@playwright/test";

import { loginAs } from "../helpers";

const OUT = "/tmp/ui-review-u0";
const HOME = "/apps/controllership-finance";

async function shot(page: Page, name: string) {
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
}

test.describe("U0 inventory", () => {
  test("home + entry-audit entrada @desktop", async ({ page }, info) => {
    test.skip(info.project.name !== "desktop", "desktop");
    await loginAs(page, "allowed");
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(HOME);
    await expect(page.getByText("Caminhos e funcionalidades")).toBeVisible({
      timeout: 45_000,
    });
    await shot(page, "home-1440-light");

    await page.goto(`${HOME}/entry-audit`);
    await expect(
      page.getByRole("heading", { name: /Auditoria de Entradas/i }).first(),
    ).toBeVisible({ timeout: 45_000 });
    await shot(page, "entry-audit-home-1440-light");

    await page.setViewportSize({ width: 1024, height: 800 });
    await shot(page, "entry-audit-home-1024-light");
    await page.setViewportSize({ width: 390, height: 844 });
    await shot(page, "entry-audit-home-390-light");
  });
});
