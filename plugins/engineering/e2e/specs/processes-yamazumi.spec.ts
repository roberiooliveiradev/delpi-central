import { test, expect, type Page } from "@playwright/test";

import {
  loginAsDev,
  trackPageErrors,
  expectNoFailures,
} from "../helpers";

/** Evidência E2E — Processos > Balanceamento de Linha (Yamazumi V3).
 *
 * Login SSO real → home do Portal Engenharia → card Processos → hub
 * → ferramenta independente (sem Ficha do Produto) → consulta do
 * roteiro oficial por código → seleção explícita de filial/estágio →
 * parâmetros + catálogo M1–M6 → Yamazumi (postos, atribuição, gráfico
 * carga × takt) → cenário B → F5 restore → limpeza confirmada →
 * exportações → dark/light × viewports do config.
 *
 * Pré-condição: credenciais de teste (DEV_PORTAL_*) e stack no ar. */

const PRODUCT_WITH_ROUTING = "90264302";
const TOOL = "/apps/engineering/processes/line-balancing";
const SHOTS = "e2e/artifacts/processes-yamazumi";

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate(
    (t) => document.documentElement.setAttribute("data-theme", t),
    theme,
  );
  await page.waitForTimeout(400);
}

async function shot(page: Page, name: string) {
  await page.screenshot({
    path: `${SHOTS}/${name}-${test.info().project.name}.png`,
    fullPage: true,
  });
}

/** FilterSelect do kit: trigger button + listbox em portal (não é
 * <select> nativo). Escolhe a opção pelo texto visível. */
async function chooseOption(
  page: Page,
  triggerLabel: string,
  optionName: RegExp,
  triggerIndex = 0,
) {
  await page
    .getByRole("button", { name: triggerLabel, exact: true })
    .nth(triggerIndex)
    .click();
  const listbox = page.getByRole("listbox");
  await expect(listbox).toBeVisible({ timeout: 10_000 });
  await listbox.getByRole("button", { name: optionName }).first().click();
  await expect(page.getByRole("listbox")).toHaveCount(0);
}

/** Abre a ferramenta, carrega o roteiro oficial e seleciona o
 * primeiro estágio disponível (contexto sempre explícito). */
async function openToolAndLoadRouting(page: Page) {
  await page.goto(TOOL);
  await expect(
    page.getByRole("heading", { name: "Balanceamento de Linha" }),
  ).toBeVisible({ timeout: 30_000 });
  await page.locator("#lb-product-code").fill(PRODUCT_WITH_ROUTING);
  await page.getByRole("button", { name: "Buscar roteiro" }).click();
  await expect(
    page.getByText(/Selecione a filial e o estágio produtivo/),
  ).toBeVisible({ timeout: 45_000 });
  await chooseOption(page, "Estágio produtivo", /^Estágio /);
  await expect(
    page.getByRole("heading", { name: "Operações oficiais do roteiro" }),
  ).toBeVisible({ timeout: 15_000 });
}

test.describe("Processos > Balanceamento de Linha — Yamazumi V3", () => {
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

  test("card Processos no Início e hub de ferramentas", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.goto("/apps/engineering");
    await expect(
      page.getByText("Processos", { exact: true }).first(),
    ).toBeVisible({ timeout: 30_000 });
    await expect(
      page.getByRole("button", { name: /Balanceamento de Linha/ }).first(),
    ).toBeVisible();
    await shot(page, "lb-home-card-dark");

    /* Hub próprio — sem passar pela Ficha do Produto. */
    await page
      .getByRole("button", { name: /Engenharia de Processos/ })
      .first()
      .click();
    await expect(page).toHaveURL(/\/apps\/engineering\/processes$/, {
      timeout: 15_000,
    });
    await expect(
      page.getByRole("heading", { name: "Engenharia de Processos" }),
    ).toBeVisible({ timeout: 15_000 });
    await shot(page, "lb-hub-dark");

    await page.getByRole("button", { name: "Abrir ferramenta" }).click();
    await expect(page).toHaveURL(/processes\/line-balancing/);
    await expect(
      page.getByRole("heading", { name: "Balanceamento de Linha" }),
    ).toBeVisible();

    /* Ferramentas futuras: planejamento sem ação falsa. */
    await page.goto("/apps/engineering/processes");
    await expect(page.getByText("Em planejamento").first()).toBeVisible();

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("consulta oficial, contexto explícito e operações deduplicadas", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await page.goto(TOOL);
    await expect(
      page.getByText(/Informe o código do produto/),
    ).toBeVisible({ timeout: 30_000 });
    await shot(page, "lb-tool-idle");

    await page.locator("#lb-product-code").fill(PRODUCT_WITH_ROUTING);
    await page.getByRole("button", { name: "Buscar roteiro" }).click();

    /* Contexto exigido: estágio precisa de seleção explícita. */
    await expect(
      page.getByText(/Selecione a filial e o estágio produtivo/),
    ).toBeVisible({ timeout: 45_000 });
    await chooseOption(page, "Estágio produtivo", /^Estágio /);
    await expect(
      page.getByRole("heading", { name: "Operações oficiais do roteiro" }),
    ).toBeVisible({ timeout: 15_000 });
    await shot(page, "lb-routing-loaded");

    /* Produto inexistente → estado honesto, nunca dados fictícios. */
    await page.locator("#lb-product-code").fill("00000000-INEXISTENTE");
    await page.getByRole("button", { name: "Buscar roteiro" }).click();
    await expect(
      page.getByText(/não encontrado|sem roteiro|vazio/i),
    ).toBeVisible({ timeout: 30_000 });
    await shot(page, "lb-not-found");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("catálogo M1–M6, análise rápida e Yamazumi interativo", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openToolAndLoadRouting(page);
    await expect(
      page.getByRole("heading", { name: /Yamazumi/ }),
    ).toBeVisible({ timeout: 15_000 });

    /* Catálogo dos seis métodos com status honesto. */
    for (const label of ["M1", "M2", "M3", "M4", "M5", "M6"]) {
      await expect(
        page.getByText(new RegExp(`${label} ·`)),
      ).toBeVisible();
    }
    await expect(
      page.getByText("Planejado").first(),
    ).toBeVisible();
    await shot(page, "lb-method-catalog");

    /* Parâmetros → análise rápida M1 via domínio. */
    await page.locator("#lb-demand").fill("500");
    await page.locator("#lb-shift").fill("480");
    await page.locator("#lb-break").fill("60");
    await chooseOption(page, "Método", /^M1\b/);
    await page
      .getByRole("button", { name: "Calcular análise rápida" })
      .click();
    await expect(page.getByText(/Resultados e cenários/)).toBeVisible({
      timeout: 45_000,
    });
    await shot(page, "lb-m1-result");

    /* Yamazumi — postos e atribuição de operações oficiais. */
    await chooseOption(page, "Método", /^M5\b/);
    await page
      .getByRole("button", { name: "Adicionar posto" })
      .click();
    await page
      .getByRole("button", { name: "Adicionar posto" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Posto 01" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Posto 02" }),
    ).toBeVisible();

    /* Atribui operações não atribuídas ao Posto 01 (controle acessível). */
    const assignTriggers = page.getByRole("button", {
      name: "Atribuir a",
      exact: true,
    });
    const count = await assignTriggers.count();
    for (let i = 0; i < Math.min(count, 3); i += 1) {
      await chooseOption(page, "Atribuir a", /^Posto/, 0);
      await page.waitForTimeout(200);
    }
    await shot(page, "lb-yamazumi-assigned");

    /* Gráfico carga × takt empilhado + linha de referência. */
    await expect(
      page.getByText(/Carga × takt por posto/),
    ).toBeVisible();
    await expect(
      page.locator(".delpi-ui-multi-type-series-chart").first(),
    ).toBeVisible();
    await shot(page, "lb-yamazumi-chart-dark");

    /* Reordenação por botão — alternativa acessível ao drag-and-drop. */
    await page
      .getByRole("button", { name: /Mover Posto 02 para cima/ })
      .click();
    await shot(page, "lb-yamazumi-reordered");

    /* Cenário B preserva o estudo A. */
    await page.getByRole("button", { name: "Novo cenário" }).click();
    await expect(
      page.getByRole("button", { name: "Cenário B" }),
    ).toBeVisible();
    await shot(page, "lb-scenario-b");

    /* F5 → estudo restaurado no mesmo contexto (sessionStorage). */
    await page.reload();
    await page.locator("#lb-product-code").fill(PRODUCT_WITH_ROUTING);
    await page.getByRole("button", { name: "Buscar roteiro" }).click();
    await expect(
      page.getByText(/Selecione a filial e o estágio produtivo/),
    ).toBeVisible({ timeout: 45_000 });
    await chooseOption(page, "Estágio produtivo", /^Estágio /);
    await expect(
      page.getByRole("button", { name: "Cenário B" }),
    ).toBeVisible({ timeout: 30_000 });
    await shot(page, "lb-restored-after-f5");

    /* Limpar estudo → confirmação → rascunho removido. */
    await page.getByRole("button", { name: "Limpar estudo" }).click();
    await expect(
      page.getByText(/Nenhum dado oficial ou rascunho da Ficha/),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Limpar rascunho" })
      .click();
    await expect(
      page.getByRole("button", { name: "Cenário B" }),
    ).toHaveCount(0);
    await shot(page, "lb-cleared");

    await setTheme(page, "light");
    await shot(page, "lb-tool-light");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("exportações do Yamazumi e responsividade", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await openToolAndLoadRouting(page);

    await page.getByRole("button", { name: "Adicionar posto" }).click();
    const assignTriggers = page.getByRole("button", {
      name: "Atribuir a",
      exact: true,
    });
    if ((await assignTriggers.count()) > 0) {
      await chooseOption(page, "Atribuir a", /^Posto/, 0);
    }
    await expect(
      page.locator(".delpi-ui-multi-type-series-chart").first(),
    ).toBeVisible({ timeout: 15_000 });

    /* CSV / Excel / PDF pelo padrão corporativo de exportação. */
    const csvBtn = page.getByRole("button", { name: /CSV/ }).first();
    const xlsxBtn = page.getByRole("button", { name: /Excel/ }).first();
    const pdfBtn = page.getByRole("button", { name: /PDF/ }).first();
    await expect(csvBtn).toBeVisible();
    const [csvDl] = await Promise.all([
      page.waitForEvent("download", { timeout: 15_000 }),
      csvBtn.click(),
    ]);
    expect(csvDl.suggestedFilename()).toMatch(/\.csv$/i);
    const [xlsxDl] = await Promise.all([
      page.waitForEvent("download", { timeout: 15_000 }),
      xlsxBtn.click(),
    ]);
    expect(xlsxDl.suggestedFilename()).toMatch(/\.xlsx$/i);
    /* PDF corporativo abre janela de impressão (popup), não download. */
    const [pdfPopup] = await Promise.all([
      page.waitForEvent("popup", { timeout: 20_000 }),
      pdfBtn.click(),
    ]);
    await pdfPopup.waitForLoadState("domcontentloaded");
    await expect(
      pdfPopup.getByText(/Yamazumi/i).first(),
    ).toBeVisible({ timeout: 15_000 });
    await pdfPopup.close();
    await shot(page, "lb-exports");

    /* Sem overflow horizontal da página no viewport atual. */
    const overflow = await page.evaluate(
      () =>
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth + 4,
    );
    expect(overflow).toBe(false);

    await expectNoFailures(pageErrors, forbiddenCalls);
  });
});
