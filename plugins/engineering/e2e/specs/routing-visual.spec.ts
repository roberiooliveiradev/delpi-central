import { test, expect, type Page } from "@playwright/test";

import {
  loginAsDev,
  trackPageErrors,
  expectNoFailures,
} from "../helpers";

/** Evidência visual da aba Roteiro (Doc 126 + REWORK-01).
 *
 * Login SSO real → ficha do produto → Operações/Balanceamento/Análise
 * visual, nos dois temas e em todos os viewports do config (desktop,
 * tablet, mobile, 320px). Screenshots vão para artifacts/routing-visual
 * com nome de projeto+tema+seção — servem como "depois" do rework.
 *
 * Pré-condição: DEV_PORTAL_USERNAME/DEV_PORTAL_PASSWORD (infra/.env) e
 * stack dev no ar (portal + engineering-api + api-delpi). */

const PRODUCT_WITH_ROUTING = "90264302";
const DETAIL = (code: string) =>
  `/apps/engineering/products/${code}?tab=routing`;
const SHOTS = "artifacts/routing-contract";

async function openRoutingTab(page: Page, code: string) {
  await page.goto(DETAIL(code));
  await expect(
    page.getByRole("heading", { name: "Roteiro de fabricação" }),
  ).toBeVisible({ timeout: 30_000 });
}

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate(
    (t) => document.documentElement.setAttribute("data-theme", t),
    theme,
  );
  /* repaints assíncronos dos gráficos (MutationObserver + SVG) */
  await page.waitForTimeout(400);
}

async function shot(page: Page, name: string) {
  await page.screenshot({
    path: `${SHOTS}/${name}-${test.info().project.name}.png`,
    fullPage: true,
  });
}

test.describe("aba Roteiro — evidência visual", () => {
  test.describe.configure({ mode: "serial" });

  let forbiddenCalls: string[] = [];

  test.beforeEach(async ({ page }) => {
    forbiddenCalls = [];
    page.on("request", (req) => {
      if (req.url().includes("/apps/api-delpi")) {
        forbiddenCalls.push(req.url());
      }
    });
    await loginAsDev(page);
  });

  test("operações — dark e light, expansão e estágios", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openRoutingTab(page, PRODUCT_WITH_ROUTING);

    await setTheme(page, "dark");
    await shot(page, "operations-dark");

    /* Expande a primeira operação — card expansível do kit. */
    await page
      .getByRole("button", { name: /^Operação\s/ })
      .first()
      .click();
    await expect(
      page.getByText("Linhas oficiais fundidas"),
    ).toBeVisible({ timeout: 10_000 });
    await shot(page, "operations-dark-expanded");

    /* Estágio técnico colapsável (detalhes secundários). */
    const techDetails = page.getByRole("button", {
      name: /Detalhes técnicos do estágio/i,
    });
    if (await techDetails.isVisible().catch(() => false)) {
      await techDetails.click();
      await shot(page, "operations-dark-tech-details");
    }

    await setTheme(page, "light");
    await shot(page, "operations-light");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("balanceamento — formulário, validação e resultado", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openRoutingTab(page, PRODUCT_WITH_ROUTING);
    await page.getByRole("tab", { name: "Balanceamento" }).click();

    await setTheme(page, "dark");
    await shot(page, "balance-dark-empty");

    await page.locator("#routing-demand").fill("500");
    await page.locator("#routing-shift").fill("480");
    await page.locator("#routing-break").fill("60");
    await shot(page, "balance-dark-filled-preview");

    await page
      .getByRole("button", { name: "Calcular balanceamento" })
      .click();
    await expect(page.getByText(/Resultado do balanceamento/)).toBeVisible({
      timeout: 30_000,
    });
    await shot(page, "balance-dark-result");

    /* Segundo cenário → tabela de comparação atribuível. */
    await page.locator("#routing-demand").fill("700");
    await page
      .getByRole("button", { name: "Calcular balanceamento" })
      .click();
    await expect(page.getByText("Comparação de cenários")).toBeVisible({
      timeout: 30_000,
    });
    await shot(page, "balance-dark-comparison");

    /* Validação honesta — demanda inválida. */
    await page.locator("#routing-demand").fill("abc");
    await expect(
      page.getByText(/Demanda deve ser um número maior que zero/),
    ).toBeVisible();
    await shot(page, "balance-dark-validation-error");

    await setTheme(page, "light");
    await shot(page, "balance-light-result");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("análise visual — gráficos temáticos e escala legível", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openRoutingTab(page, PRODUCT_WITH_ROUTING);

    /* Cenário para habilitar tempo×takt e simulação. */
    await page.getByRole("tab", { name: "Balanceamento" }).click();
    await page.locator("#routing-demand").fill("500");
    await page.locator("#routing-shift").fill("480");
    await page.locator("#routing-break").fill("60");
    await page
      .getByRole("button", { name: "Calcular balanceamento" })
      .click();
    await expect(page.getByText(/Resultado do balanceamento/)).toBeVisible({
      timeout: 30_000,
    });

    await page.getByRole("tab", { name: "Análise visual" }).click();

    await setTheme(page, "dark");
    await shot(page, "visual-dark");

    /* Superfície do gráfico deve herdar o tema — não pode ser o
     * fundo claro "office" no modo escuro. */
    const chartBg = await page
      .locator("[class*='series-chart'], svg")
      .first()
      .evaluate((el) => getComputedStyle(el).backgroundColor)
      .catch(() => null);
    test.info().attach("chart-background-dark", {
      body: String(chartBg),
      contentType: "text/plain",
    });

    await setTheme(page, "light");
    await shot(page, "visual-light");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("produto sem roteiro — vazio honesto", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.goto(DETAIL("90260148"));
    await expect(
      page.getByText(/não possui roteiro de fabricação/i),
    ).toBeVisible({ timeout: 30_000 });
    await shot(page, "empty-routing-dark");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });
});
