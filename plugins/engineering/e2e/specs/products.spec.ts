import { expect, test } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const LIST_PATH = "/apps/engineering/products";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

test("catálogo do Início exibe Produtos com ícone e navega", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto("/apps/engineering");

  const card = page
    .locator("a, button")
    .filter({ hasText: "Produtos" })
    .first();
  await expect(card).toBeVisible({ timeout: 20_000 });
  await expect(card.locator("svg").first()).toBeVisible();

  await card.click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/?$/);
  await expect(
    page.getByRole("heading", { name: "Catálogo de produtos", level: 1 }),
  ).toBeVisible({ timeout: 20_000 });

  expectNoFailures(forbidden, pageErrors);
});

test("listagem renderiza filtros reativos, multiselects e Limpar", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);

  await expect(
    page.getByRole("group", { name: "Filtros de produtos" }),
  ).toBeVisible();
  // Limpar só aparece quando existe filtro aplicado (slot superior do hero).
  const clearButton = page.getByRole("button", { name: "Limpar filtros" });
  await expect(clearButton).toHaveCount(0);
  // Busca reativa — não existe botão Filtrar.
  await expect(
    page.getByRole("button", { name: "Filtrar", exact: true }),
  ).toHaveCount(0);

  // Multiselects oficiais de Grupo e Tipo.
  const triggers = page.locator('button[aria-haspopup="listbox"]');
  await expect(triggers).toHaveCount(2, { timeout: 20_000 });

  // Resultado oficial OU estado honesto — nunca tela quebrada.
  const table = page.locator("table");
  const settled = await Promise.race([
    table.waitFor({ state: "visible", timeout: 30_000 }).then(() => "table"),
    page
      .getByText("Nenhum produto encontrado para os filtros aplicados.")
      .waitFor({ state: "visible", timeout: 30_000 })
      .then(() => "empty"),
    page
      .getByText(/Catálogo de produtos indisponível|Acesso negado|indisponível/)
      .first()
      .waitFor({ state: "visible", timeout: 30_000 })
      .then(() => "state"),
  ]);
  expect(["table", "empty", "state"]).toContain(settled);

  if (settled === "table") {
    await expect(table.locator("thead").getByText("Código")).toBeVisible();
    await expect(table.locator("thead").getByText("Descrição")).toBeVisible();
    await expect(table.locator("thead").getByText("Situação")).toBeVisible();
    // Tabela fill-height: registros rolam dentro do wrap oficial.
    await expect(
      page.locator(".delpi-ui-table-wrap--scroll"),
    ).toBeVisible();
    // Paginação fora da área rolável.
    await expect(
      page.getByRole("navigation", { name: "Paginação" }),
    ).toBeVisible();
  }

  // Filtro aplicado → Limpar aparece; limpar → some novamente.
  await page.getByPlaceholder("Código do produto").fill("Z");
  await expect(clearButton).toBeVisible({ timeout: 10_000 });
  await clearButton.click();
  await expect(clearButton).toHaveCount(0, { timeout: 10_000 });

  expectNoFailures(forbidden, pageErrors);
});

test("busca por código é reativa e sincroniza a URL", async ({ page }) => {
  await page.goto(LIST_PATH);
  await expect(
    page.getByRole("group", { name: "Filtros de produtos" }),
  ).toBeVisible({ timeout: 30_000 });

  const codeField = page.getByPlaceholder("Código do produto");
  await codeField.fill("ZZZ-NAO-EXISTE-TESTE");

  // Debounce → URL reflete o filtro sem ação explícita.
  await expect(page).toHaveURL(/code=ZZZ-NAO-EXISTE-TESTE/, {
    timeout: 10_000,
  });

  // Filtro impossível → vazio honesto (ou estado oficial de indisponível).
  const outcome = await Promise.race([
    page
      .getByText("Nenhum produto encontrado para os filtros aplicados.")
      .waitFor({ state: "visible", timeout: 45_000 })
      .then(() => "empty"),
    page
      .getByText(/indisponível|Acesso negado/)
      .first()
      .waitFor({ state: "visible", timeout: 45_000 })
      .then(() => "state"),
  ]);
  expect(["empty", "state"]).toContain(outcome);

  // Limpar restaura URL e filtros.
  await page.getByRole("button", { name: "Limpar filtros" }).click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/?$/);
  await expect(codeField).toHaveValue("");
});

test("multiselect de Tipo aplica seleção na URL", async ({ page }) => {
  await page.goto(LIST_PATH);
  await expect(
    page.getByRole("group", { name: "Filtros de produtos" }),
  ).toBeVisible({ timeout: 30_000 });

  const triggers = page.locator('button[aria-haspopup="listbox"]');
  await expect(triggers).toHaveCount(2, { timeout: 20_000 });

  // Segundo trigger = Tipo.
  const typeTrigger = triggers.nth(1);
  await typeTrigger.click();

  const listbox = page.getByRole("listbox");
  await expect(listbox).toBeVisible({ timeout: 15_000 });

  const optionLabels = listbox.locator("li label");
  const count = await optionLabels.count();
  test.skip(count === 0, "Catálogo de tipos indisponível neste ambiente.");

  // Seleciona a primeira opção oficial — commit imediato na URL.
  await optionLabels.nth(0).click({ timeout: 10_000 });

  await expect(page).toHaveURL(/types=/, { timeout: 10_000 });

  // Limpar também remove seleções múltiplas.
  await page.getByRole("button", { name: "Limpar filtros" }).click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/?$/);
});

test("filtros avançados: draft, aplicar atômico, chip e Limpar global", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);
  const filtersTrigger = page.getByRole("button", {
    name: "Filtros",
    exact: true,
  });
  await expect(filtersTrigger).toBeVisible({ timeout: 30_000 });

  // Draft não dispara consulta: abrir, adicionar critério e fechar sem
  // aplicar não altera a URL.
  await filtersTrigger.click();
  const panel = page.getByRole("dialog", { name: "Filtros avançados" });
  await expect(panel).toBeVisible();
  await expect(
    panel.getByText("Refine os produtos combinando um ou mais critérios."),
  ).toBeVisible();
  await panel
    .getByRole("button", { name: "Adicionar critério" })
    .click();
  await expect(panel.locator(".engineering-products__adv-rule")).toHaveCount(
    1,
  );
  await page.keyboard.press("Escape");
  await expect(panel).toBeHidden({ timeout: 10_000 });
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/?$/);

  // Critério de subgrupo (campo sem controle no hero) → Apply atômico:
  // URL sub=, chip removível visível e badge no gatilho.
  await filtersTrigger.click();
  await panel
    .getByRole("button", { name: "Adicionar critério" })
    .click();
  const fieldSelect = panel.getByRole("button", { name: "Campo" });
  await fieldSelect.click();
  await page
    .getByRole("listbox")
    .getByRole("button", { name: "Subgrupo" })
    .click();
  await panel.getByPlaceholder("Ex.: 01").fill("ZZTESTE");
  await panel.getByRole("button", { name: "Aplicar filtros" }).click();

  await expect(page).toHaveURL(/sub=ZZTESTE/, { timeout: 15_000 });
  await expect(panel).toBeHidden();
  const chip = page.getByRole("button", { name: /Subgrupo: ZZTESTE/ });
  await expect(chip).toBeVisible();

  // Remover o chip volta a consultar sem o critério.
  await chip.click();
  await expect(page).not.toHaveURL(/sub=/, { timeout: 15_000 });
  await expect(chip).toHaveCount(0);

  // Limpar global também remove critérios aplicados via painel.
  await filtersTrigger.click();
  await panel
    .getByRole("button", { name: "Adicionar critério" })
    .click();
  await panel.getByPlaceholder("Ex.: 100").fill("77");
  await panel.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(page).toHaveURL(/code=77/, { timeout: 15_000 });
  await page.getByRole("button", { name: "Limpar filtros" }).click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/?$/);

  expectNoFailures(forbidden, pageErrors);
});

test("gerenciador de colunas: opcionais oficiais, toggle e restaurar", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);
  const table = page.locator("table");
  const hasRows = await table
    .waitFor({ state: "visible", timeout: 30_000 })
    .then(() => true)
    .catch(() => false);
  test.skip(!hasRows, "Catálogo dev sem linhas — gerenciador exige tabela.");

  // Colunas opcionais do contrato view=engineering começam ocultas.
  const thead = table.locator("thead");
  await expect(thead.getByText("Subgrupo")).toHaveCount(0);
  await expect(thead.getByText("Cód. barras")).toHaveCount(0);

  const columnsTrigger = page.getByRole("button", {
    name: "Colunas",
    exact: true,
  });
  await columnsTrigger.click();
  const columnsPanel = page.getByRole("dialog", {
    name: "Colunas visíveis",
  });
  await expect(columnsPanel).toBeVisible({ timeout: 10_000 });
  await expect(columnsPanel.getByText("Subgrupo")).toBeVisible();
  await expect(columnsPanel.getByText("Cód. barras")).toBeVisible();
  await expect(columnsPanel.getByText("Desenho")).toBeVisible();

  // Exibe uma opcional → cabeçalho aparece na tabela.
  await columnsPanel
    .getByLabel("Exibir coluna Subgrupo")
    .click();
  await expect(thead.getByText("Subgrupo")).toBeVisible({ timeout: 10_000 });

  // Restaurar padrão oculta novamente as opcionais.
  await columnsPanel
    .getByRole("button", { name: "Restaurar" })
    .click();
  await expect(thead.getByText("Subgrupo")).toHaveCount(0);

  expectNoFailures(forbidden, pageErrors);
});

test("ficha do produto renderiza abas oficiais com URL (?tab=)", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);

  const firstRow = page.locator("table tbody tr").first();
  const hasRows = await firstRow
    .waitFor({ state: "visible", timeout: 30_000 })
    .then(() => true)
    .catch(() => false);
  test.skip(!hasRows, "Catálogo dev sem linhas — estado vazio já coberto.");

  await firstRow.click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/.+/);
  await expect(
    page.getByRole("heading", { name: "Ficha do Produto", level: 1 }),
  ).toBeVisible({ timeout: 30_000 });

  // Seis abas oficiais na ordem da spec 61.
  const tabs = page.getByRole("tab");
  await expect(tabs).toHaveCount(6, { timeout: 30_000 });
  for (const label of [
    "Visão geral",
    "Estrutura",
    "Onde é usado",
    "Fornecedores",
    "Desenhos",
    "Histórico",
  ]) {
    await expect(
      page.getByRole("tab", { name: label }),
    ).toBeVisible();
  }

  // Modo Editar honestamente bloqueado (sem contrato WRITE — doc 63 §2.8).
  const editButton = page.getByRole("button", { name: /Editar/ }).first();
  await expect(editButton).toBeVisible();
  await expect(editButton).toBeDisabled();

  // Troca de aba → URL com ?tab= (histórico navegável).
  await page.getByRole("tab", { name: "Estrutura" }).click();
  await expect(
    page.getByRole("tab", { name: "Estrutura" }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(page).toHaveURL(/tab=structure/);

  // Voltar → retorna à aba anterior.
  await page.goBack();
  await expect(page).not.toHaveURL(/tab=structure/, { timeout: 15_000 });

  // Avançar → aba volta.
  await page.goForward();
  await expect(page).toHaveURL(/tab=structure/, { timeout: 15_000 });

  // Aba inválida → normaliza para Visão geral (URL corrigida).
  const invalidUrl = page
    .url()
    .replace(/tab=\w+/, "tab=inexistente");
  await page.goto(invalidUrl);
  await expect(
    page.getByRole("tab", { name: "Visão geral" }),
  ).toHaveAttribute("aria-selected", "true", { timeout: 20_000 });

  // Deep link direto em aba específica.
  const base = page.url().split("?")[0];
  await page.goto(`${base}?tab=suppliers`);
  await expect(
    page.getByRole("tab", { name: "Fornecedores" }),
  ).toHaveAttribute("aria-selected", "true", { timeout: 20_000 });

  // Estrutura: árvore oficial colapsável OU estado vazio honesto.
  await page.goto(`${base}?tab=structure`);
  const treeOutcome = await Promise.race([
    page
      .locator(".lmps-rich-tree")
      .waitFor({ state: "visible", timeout: 45_000 })
      .then(() => "tree"),
    page
      .getByText(/não possui estrutura cadastrada|Estrutura indisponível|Acesso negado/)
      .first()
      .waitFor({ state: "visible", timeout: 45_000 })
      .then(() => "state"),
  ]);
  expect(["tree", "state"]).toContain(treeOutcome);
  if (treeOutcome === "tree") {
    // Card R2: título oficial + toolbar Expandir/Recolher todos.
    await expect(
      page.getByText("Estrutura do produto").first(),
    ).toBeVisible();
    const expandAll = page.getByRole("button", {
      name: "Expandir todos",
    });
    const collapseAll = page.getByRole("button", {
      name: "Recolher todos",
    });
    await expect(collapseAll).toBeVisible();
    // Nós com filhos expandem/recolhem via toggle oficial (aria-expanded).
    const toggles = page.locator(".lmps-rich-tree__toggle");
    const toggleCount = await toggles.count();
    if (toggleCount > 0) {
      const first = toggles.first();
      const wasExpanded =
        (await first.getAttribute("aria-expanded")) === "true";
      await first.click();
      await expect(first).toHaveAttribute(
        "aria-expanded",
        wasExpanded ? "false" : "true",
      );
    }
    // Recolher todos: somente a raiz permanece expandida.
    await collapseAll.click();
    const expandedCount = await page
      .locator('.lmps-rich-tree__toggle[aria-expanded="true"]')
      .count();
    expect(expandedCount).toBeLessThanOrEqual(1);
    // Expandir todos (quando dentro do teto de segurança) reabre ramos.
    if (await expandAll.isEnabled().catch(() => false)) {
      await expandAll.click();
      const expandedAfter = await page
        .locator('.lmps-rich-tree__toggle[aria-expanded="true"]')
        .count();
      expect(expandedAfter).toBeGreaterThan(0);
    }
  }

  // Desenhos: preview oficial carrega automaticamente OU estado honesto.
  await page.goto(`${base}?tab=drawings`);
  const drawOutcome = await Promise.race([
    page
      .locator(".delpi-ui-file-preview__pdf")
      .waitFor({ state: "visible", timeout: 60_000 })
      .then(() => "pdf"),
    page
      .getByText(/não possui desenho|desenho técnico|indisponível|Acesso negado/)
      .first()
      .waitFor({ state: "visible", timeout: 60_000 })
      .then(() => "state"),
  ]);
  expect(["pdf", "state"]).toContain(drawOutcome);
  if (drawOutcome === "pdf") {
    // Workspace R2: cabeçalho compacto de metadados + viewer ampliado.
    await expect(
      page.locator(".engineering-product-drawing__bar"),
    ).toBeVisible();
    await expect(
      page.locator(".engineering-product-drawing__meta"),
    ).toContainText("Arquivo");
    await expect(
      page.locator(".engineering-product-drawing__meta"),
    ).toContainText("Revisão");
    await expect(
      page.getByRole("button", { name: "Abrir ampliado" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Baixar PDF" }),
    ).toBeVisible();
  }

  expectNoFailures(forbidden, pageErrors);
});
