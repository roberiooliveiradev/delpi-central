import { test, expect, type Page } from "@playwright/test";

import {
  loginAsDev,
  trackPageErrors,
  expectNoFailures,
} from "../helpers";

/** Evidência visual da aba Roteiro — Routing Study Workspace V2.
 *
 * Login SSO real → ficha do produto → página única scrollável
 * (sem tabs internas): operações → estudo → resultados → análise
 * visual. Cobre rascunho de sessão (refresh/restore), postos
 * hipotéticos, cenários e limpeza confirmada — dark/light ×
 * viewports do config. Screenshots em artifacts/routing-contract.
 *
 * Pré-condição: credenciais de teste (DEV_PORTAL_USERNAME /
 * DEV_PORTAL_PASSWORD em infra/.env) e stack no ar. */

const PRODUCT_WITH_ROUTING = "90264302";
const DETAIL = (code: string) =>
  `/apps/engineering/products/${code}?tab=routing`;
const SHOTS = "artifacts/routing-contract";

async function openRoutingTab(page: Page, code: string) {
  await page.goto(DETAIL(code));
  await expect(
    page.getByRole("heading", { name: "Roteiro de fabricação" }),
  ).toBeVisible({ timeout: 30_000 });
  await expect(
    page.getByRole("heading", { name: "Estudo de balanceamento" }),
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

async function fillConditions(page: Page) {
  await page.locator("#routing-demand").fill("500");
  await page.locator("#routing-shift").fill("480");
  await page.locator("#routing-break").fill("60");
}

test.describe("aba Roteiro V2 — evidência visual", () => {
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

  test("página única — operações dark/light, expansão e sem tabs internas", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openRoutingTab(page, PRODUCT_WITH_ROUTING);

    /* V2: sem navegação interna — todas as seções no scroll. */
    await expect(page.getByRole("tab")).toHaveCount(0);
    await expect(
      page.getByRole("heading", { name: "Operações do estágio" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Análise visual" }),
    ).toBeVisible();

    await setTheme(page, "dark");
    await shot(page, "v2-page-dark-top");

    /* Expande a primeira operação — card expansível do kit. */
    await page
      .getByRole("button", { name: /^Operação\s/ })
      .first()
      .click();
    await expect(
      page.getByText("Linhas oficiais fundidas"),
    ).toBeVisible({ timeout: 10_000 });
    await shot(page, "v2-operations-dark-expanded");

    /* Estágio técnico colapsável (detalhes secundários). */
    const techDetails = page.getByRole("button", {
      name: /Detalhes técnicos do estágio/i,
    });
    if (await techDetails.isVisible().catch(() => false)) {
      await techDetails.click();
      await shot(page, "v2-operations-dark-tech-details");
    }

    await setTheme(page, "light");
    await shot(page, "v2-page-light");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("estudo — formulário, validação, resultado e cenários A/B", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openRoutingTab(page, PRODUCT_WITH_ROUTING);

    await setTheme(page, "dark");
    await shot(page, "v2-study-dark-empty");

    await fillConditions(page);
    await shot(page, "v2-study-dark-filled-preview");

    await page
      .getByRole("button", { name: "Calcular análise rápida" })
      .click();
    await expect(page.getByText(/Resultados e cenários/)).toBeVisible({
      timeout: 30_000,
    });
    await shot(page, "v2-study-dark-result");

    /* Novo cenário preserva o anterior — A e B identificáveis. */
    await page.getByRole("button", { name: "Novo cenário" }).click();
    await expect(page.getByText("Cenário B")).toBeVisible();
    await page.locator("#routing-demand").fill("700");
    await page
      .getByRole("button", { name: "Calcular análise rápida" })
      .click();
    await expect(
      page.getByRole("cell", { name: "Cenário A" }),
    ).toBeVisible({ timeout: 30_000 });
    /* Resultado de B recém-calculado — nada de STALE em resultado fresco. */
    await expect(page.getByText("STALE")).toHaveCount(0);
    await shot(page, "v2-study-dark-comparison");

    /* Validação honesta — demanda inválida. */
    await page.locator("#routing-demand").fill("abc");
    await expect(
      page.getByText(/Demanda deve ser um número maior que zero/),
    ).toBeVisible();
    await shot(page, "v2-study-dark-validation-error");

    await setTheme(page, "light");
    await shot(page, "v2-study-light-result");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("configurar postos — cards hipotéticos e limitação explícita", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openRoutingTab(page, PRODUCT_WITH_ROUTING);

    await page
      .getByRole("button", { name: "Configurar postos" })
      .click();
    await expect(page.getByText(/DRAFT_LOCAL/)).toBeVisible();
    await shot(page, "v2-posts-dark-empty");

    await page.getByRole("button", { name: "Adicionar posto" }).click();
    await expect(page.getByText("Posto 01")).toBeVisible();
    await page.getByRole("button", { name: "Adicionar posto" }).click();
    await expect(page.getByText("Posto 02")).toBeVisible();
    await shot(page, "v2-posts-dark-two");

    /* Reordenação por botão — acessível sem drag-and-drop. */
    await page
      .getByRole("button", { name: /Mover Posto 02 para cima/ })
      .click();
    await shot(page, "v2-posts-dark-reordered");

    /* Aviso: análise rápida não valida a distribuição manual. */
    await expect(
      page.getByText(/não valida a distribuição manual/),
    ).toBeVisible();

    await setTheme(page, "light");
    await shot(page, "v2-posts-light");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("rascunho de sessão — persistir, refresh, recuperar e limpar", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openRoutingTab(page, PRODUCT_WITH_ROUTING);

    await fillConditions(page);
    await expect(page.getByText("Salvo nesta aba")).toBeVisible({
      timeout: 10_000,
    });

    /* Refresh → rascunho recuperado na mesma aba. */
    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Estudo de balanceamento" }),
    ).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/Rascunho recuperado/)).toBeVisible();
    await expect(page.locator("#routing-demand")).toHaveValue("500");
    await expect(page.locator("#routing-shift")).toHaveValue("480");
    await shot(page, "v2-study-restored");

    /* Limpar — cancelar preserva tudo. */
    await page.getByRole("button", { name: "Limpar estudo" }).click();
    await expect(
      page.getByText(/Não altera roteiro, BOM, ERP/),
    ).toBeVisible();
    await shot(page, "v2-clear-dialog");
    await page.getByRole("button", { name: "Cancelar" }).click();
    await expect(page.locator("#routing-demand")).toHaveValue("500");

    /* Limpar — confirmar zera só o rascunho do contexto. */
    await page.getByRole("button", { name: "Limpar estudo" }).click();
    await page
      .getByRole("button", { name: "Limpar estudo" })
      .last()
      .click();
    await expect(page.locator("#routing-demand")).toHaveValue("");
    await expect(page.getByText(/Estudo limpo nesta aba/)).toBeVisible();

    /* O roteiro oficial permanece — operações ainda visíveis. */
    await expect(
      page.getByRole("heading", { name: "Operações do estágio" }),
    ).toBeVisible();

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("análise visual — gráficos contextuais temáticos", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openRoutingTab(page, PRODUCT_WITH_ROUTING);

    /* Sem cálculo: tempo por peça visível; takt/distribuição ocultos. */
    await expect(
      page.getByRole("heading", { name: "Análise visual" }),
    ).toBeVisible();
    await shot(page, "v2-visual-dark-no-result");

    /* Cenário para habilitar tempo×takt e simulação. */
    await fillConditions(page);
    await page
      .getByRole("button", { name: "Calcular análise rápida" })
      .click();
    await expect(page.getByText(/Resultados e cenários/)).toBeVisible({
      timeout: 30_000,
    });

    await setTheme(page, "dark");
    await shot(page, "v2-visual-dark");

    /* Superfície do gráfico deve herdar o tema — não o fundo claro
     * "office" no modo escuro. */
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
    await shot(page, "v2-visual-light");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("produto sem roteiro — vazio honesto", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.goto(DETAIL("90260148"));
    await expect(
      page.getByText(/não possui roteiro de fabricação/i),
    ).toBeVisible({ timeout: 30_000 });
    await shot(page, "v2-empty-routing-dark");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });
});
