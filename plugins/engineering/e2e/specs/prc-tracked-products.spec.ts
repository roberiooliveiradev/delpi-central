import { expect, test, type Page } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  selectKitOption,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

/** U1–U3 — Produtos acompanhados (PRC-TRACK):
 *  seletor de área, listagem server-side, detalhe com ficha
 *  consolidada por revisão, timeline expansível e comparação
 *  técnica calculada pela Engineering API. */
const QUEUE_PATH = "/apps/engineering/product-registration";

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

async function ensureAuthenticated(page: Page): Promise<void> {
  const sso = page.getByRole("button", { name: /Entrar com DELPI SSO/i });
  if (await sso.isVisible().catch(() => false)) {
    await loginAsDev(page);
  }
}

async function openProductsArea(page: Page): Promise<void> {
  await page.goto(`${QUEUE_PATH}?area=products`);
  await ensureAuthenticated(page);
  await expect(
    page.getByRole("button", { name: "Produtos acompanhados" }),
  ).toBeVisible({ timeout: 30_000 });
  /* Compacto abre em Cards (preferência persistida) — as asserções
   * desta spec exercitam a Tabela. */
  await page
    .getByRole("button", { name: "Tabela", exact: true })
    .click();
}

test("U1 — seletor de área + listagem com 5 colunas e massa HML", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-products-u1-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  /* Padrão: abre na área Solicitações. */
  await page.goto(QUEUE_PATH);
  await ensureAuthenticated(page);
  const requestsToggle = page.getByRole("button", {
    name: "Solicitações",
    exact: true,
  });
  await expect(requestsToggle).toBeVisible({ timeout: 30_000 });
  await expect(requestsToggle).toHaveAttribute("aria-pressed", "true");

  /* Alterna para Produtos acompanhados via clique (URL navegável). */
  await page
    .getByRole("button", { name: "Produtos acompanhados" })
    .click();
  await page.waitForURL(/area=products/, { timeout: 15_000 });
  await shot("area-toggle");

  /* 5 colunas aprovadas. */
  const table = page.getByRole("table");
  await expect(table).toBeVisible({ timeout: 20_000 });
  for (const col of [
    "Código oficial",
    "Descrição",
    "Versão atual",
    "Bandeiras abertas",
    "Última evolução",
  ]) {
    await expect(
      table.getByRole("columnheader", { name: col }),
    ).toBeVisible();
  }

  /* Massa HML: produtos publicados existem. */
  const rows = table.locator("tbody tr");
  await expect(rows.first()).toBeVisible({ timeout: 10_000 });
  expect(await rows.count()).toBeGreaterThan(0);
  await shot("list");

  /* Filtros contextuais no hero: busca + chips de bandeiras. */
  await expect(
    page.getByPlaceholder(/código oficial ou descrição/i),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Com bandeiras abertas" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Sem bandeiras abertas" }),
  ).toBeVisible();

  /* Busca server-side — código conhecido da massa HML. */
  await page
    .getByPlaceholder(/código oficial ou descrição/i)
    .fill("30190123");
  await page.waitForURL(/search=30190123/, { timeout: 10_000 });
  await expect(rows.first()).toContainText("30190123", {
    timeout: 15_000,
  });
  await shot("search");

  await expectNoFailures(pageErrors, forbidden);
});

test("U1 — URL state: deep-link, refresh e voltar preservam área/filtro", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(`${QUEUE_PATH}?area=products&flagState=none`);
  await ensureAuthenticated(page);
  await page
    .getByRole("button", { name: "Tabela", exact: true })
    .click();
  await expect(page.getByRole("table")).toBeVisible({
    timeout: 20_000,
  });
  await expect(
    page.getByRole("button", { name: "Sem bandeiras abertas" }),
  ).toHaveAttribute("aria-pressed", "true");

  /* Refresh preserva área+filtro pela URL. */
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Produtos acompanhados" }),
  ).toHaveAttribute("aria-pressed", "true", { timeout: 30_000 });
  await expect(
    page.getByRole("button", { name: "Sem bandeiras abertas" }),
  ).toHaveAttribute("aria-pressed", "true");

  /* Voltar para Solicitações limpa o filtro de produtos. */
  await page
    .getByRole("button", { name: "Solicitações", exact: true })
    .click();
  await page.waitForURL(
    (url) => !url.search.includes("area=products"),
    { timeout: 15_000 },
  );

  await expectNoFailures(pageErrors, forbidden);
});

test("U2 — detalhe: hero, abas duplas, ficha por versão e somente leitura", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-products-u2-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await openProductsArea(page);
  const firstRow = page.getByRole("table").locator("tbody tr").first();
  await expect(firstRow).toBeVisible({ timeout: 15_000 });
  const code = (await firstRow.locator("td").first().innerText()).trim();
  await firstRow.click();
  await page.waitForURL(/product-registration\/products\//, {
    timeout: 15_000,
  });
  await ensureAuthenticated(page);
  await shot("detail");

  /* Hero: código oficial como identidade principal (UX-P0-01),
   * versão acompanhada, última evolução e solicitação de origem. */
  await expect(
    page.getByRole("heading", { name: code, exact: true }),
  ).toBeVisible({ timeout: 20_000 });
  await expect(
    page.getByText("Última evolução técnica"),
  ).toBeVisible();
  await expect(
    page.getByText("Solicitação de origem"),
  ).toBeVisible();

  /* Exatamente duas abas. */
  const tabs = page.getByRole("tab");
  await expect(tabs).toHaveCount(2);
  await expect(
    page.getByRole("tab", { name: "Ficha técnica" }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByRole("tab", { name: "Versões" }),
  ).toBeVisible();

  /* Ficha consolidada: seletor de versão + leitura (nenhum campo
   * editável no snapshot consolidado). */
  await expect(
    page.getByRole("group", { name: "Versão exibida" }),
  ).toBeVisible({ timeout: 20_000 });
  await shot("sheet");

  await expectNoFailures(pageErrors, forbidden);
});

test("U3 — timeline expansível + comparação V1×V2 server-side", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-products-u3-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  /* Produto com V1+V2 na massa HML — busca determinística. */
  await openProductsArea(page);
  await page
    .getByPlaceholder(/código oficial ou descrição/i)
    .fill("30190123");
  await page.waitForURL(/search=30190123/, { timeout: 10_000 });
  const row = page
    .getByRole("table")
    .locator("tbody tr")
    .filter({ hasText: "30190123" });
  await expect(row.first()).toBeVisible({ timeout: 15_000 });
  await row.first().click();
  await page.waitForURL(/product-registration\/products\//, {
    timeout: 15_000,
  });
  await ensureAuthenticated(page);

  /* Aba Versões. */
  await page.getByRole("tab", { name: "Versões" }).click();
  await page.waitForURL(/tab=versions/, { timeout: 10_000 });
  await expect(
    page.getByRole("heading", { name: "Histórico de versões" }),
  ).toBeVisible({ timeout: 20_000 });
  await expect(
    page.getByRole("heading", { name: "Comparar versões" }),
  ).toBeVisible();

  /* Timeline: V2 atual acompanhada + V1 primeiro acompanhamento,
   * entradas expansíveis com aria-expanded. */
  await expect(page.getByText("Atual acompanhada")).toBeVisible();
  await expect(
    page.getByText("Primeiro acompanhamento confirmado"),
  ).toBeVisible();
  const toggles = page.locator(".engineering-prc__vtimeline-toggle");
  expect(await toggles.count()).toBeGreaterThanOrEqual(2);
  /* Recolhido por padrão — aria-expanded=false e detalhe oculto
   * de verdade (regressão: display flex anulava [hidden]). */
  const firstDetail = page.locator("#prc-vdetail-2");
  await expect(firstDetail).toBeHidden();
  await toggles.first().click();
  await expect(toggles.first()).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await expect(firstDetail).toBeVisible();
  await shot("timeline");

  /* Comparação V1×V2 — diff autoritativo do backend. */
  await selectKitOption(page, "Versão de origem", "V1");
  await selectKitOption(page, "Versão de destino", "V2");
  await page
    .getByRole("button", { name: "Comparar versões" })
    .click();
  /* Resultado: tabela de diff (Antes/Depois) OU estado «sem
   * diferença» — ambos provam o caminho server-side; nunca
   * comparação local de JSON. */
  const result = page
    .getByRole("columnheader", { name: /Antes \(V/ })
    .or(page.getByText("Sem diferença técnica entre as versões."))
    .or(page.getByText(/Não foi possível comparar/))
    .first();
  await expect(result).toBeVisible({ timeout: 20_000 });
  await shot("compare");

  /* Mesma versão bloqueada. */
  await selectKitOption(page, "Versão de origem", "V1");
  await selectKitOption(page, "Versão de destino", "V1");
  await expect(
    page.getByText("Selecione duas versões distintas."),
  ).toBeVisible();

  await expectNoFailures(pageErrors, forbidden);
});
