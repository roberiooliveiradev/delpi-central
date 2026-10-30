import { expect, test } from "@playwright/test";

import { loginAsDev } from "../helpers";

/** ENGINEERING.NC.ICON.R1 — o item "Não conformidades" no catálogo da
 *  Home deve renderizar o ícone lucide (svg) como os demais itens. */

test.describe("Portal Engenharia — ícone Não conformidades", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDev(page);
    await page.goto("/apps/engineering");
    await expect(
      page.getByText("Não conformidades").first(),
    ).toBeVisible({ timeout: 30_000 });
  });

  test("item Não conformidades exibe ícone no catálogo da Home", async ({
    page,
  }) => {
    const ncItem = page
      .locator("a, button, [role='link'], [role='button'], li")
      .filter({ hasText: /^Não conformidades$/ })
      .first();
    await expect(ncItem).toBeVisible();
    const svg = ncItem.locator("svg").first();
    await expect(svg).toBeVisible();
  });

  test("todos os itens de rota do catálogo exibem ícone (paridade)", async ({
    page,
  }) => {
    for (const label of ["LMPs", "Não conformidades"]) {
      const item = page
        .locator("a, button, [role='link'], [role='button'], li")
        .filter({ hasText: new RegExp(`^${label}$`) })
        .first();
      await expect(item.locator("svg").first()).toBeVisible();
    }
  });
});
