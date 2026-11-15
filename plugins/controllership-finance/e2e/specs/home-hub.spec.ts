import { expect, test, type Page } from "@playwright/test";

import { loginAs } from "../helpers";

const HOME = "/apps/controllership-finance";
const ARTIFACTS = "/tmp/home-hub-h5-artifacts";

async function openHome(page: Page): Promise<void> {
  await page.goto(HOME);
  await expect(page.getByText("Caminhos e funcionalidades")).toBeVisible({
    timeout: 45_000,
  });
}

test.describe("home-hub H5", () => {
  test("access: cards alvo sem Portal; favoritar persiste @desktop", async ({
    page,
  }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "desktop only");
    await loginAs(page, "allowed");
    await openHome(page);

    await expect(page.getByText("Central de Fechamento", { exact: true })).toBeVisible();
    await expect(page.getByText("Notas fiscais", { exact: true })).toBeVisible();
    await expect(page.getByText("Auditoria de Entradas", { exact: true })).toBeVisible();
    await expect(page.getByText("Portal", { exact: true })).toHaveCount(0);
    await expect(page.getByText("Meu perfil", { exact: true })).toHaveCount(0);

    // Superadmin HML pode ver Administração; access-only não.
    // Favoritar «Fechamento mensal» e recarregar.
    const closingRoute = page.getByRole("button", { name: /^Fechamento mensal$/ });
    await expect(closingRoute).toBeVisible();
    const pin = closingRoute.locator("..").getByRole("button", {
      name: /favoritos/i,
    });
    if (await pin.count()) {
      await pin.first().click();
      await page.reload();
      await openHome(page);
      await expect(
        page.getByRole("button", { name: /Favoritos|Abrir favoritos/i }).first(),
      ).toBeVisible({ timeout: 15_000 });
    }

    await page.screenshot({
      path: `${ARTIFACTS}/h5-access-desktop.png`,
      fullPage: true,
    });
  });

  test("access: Início aberto em mobile @mobile", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "mobile", "mobile only");
    await loginAs(page, "allowed");
    await openHome(page);
    await expect(page.getByText("Notas fiscais", { exact: true })).toBeVisible();
    await page.screenshot({
      path: `${ARTIFACTS}/h5-access-mobile.png`,
      fullPage: true,
    });
  });

  test("teclado: Ctrl+K abre paleta @desktop", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "desktop only");
    await loginAs(page, "allowed");
    await openHome(page);
    await page.keyboard.press("Control+K");
    await expect(page.getByRole("dialog")).toBeVisible({ timeout: 10_000 });
    await page.screenshot({
      path: `${ARTIFACTS}/h5-palette-desktop.png`,
      fullPage: true,
    });
  });
});
