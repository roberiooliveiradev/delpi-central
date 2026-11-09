import { expect, test, type Page } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const CREATE_PATH = "/apps/engineering/product-registration/new";
const UPDATE_PRODUCT = "90264270"; // produto DEV com vínculo SA5 real

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

async function gotoSheetStep(page: Page) {
  await page.goto(CREATE_PATH);
  await page.getByRole("button", { name: "Avançar" }).click();
  await expect(
    page.getByRole("button", { name: "Ficha técnica" }).first(),
  ).toBeVisible({ timeout: 20_000 });
}

async function expectWithinViewport(locator: ReturnType<Page["locator"]>) {
  const box = await locator.boundingBox();
  expect(box, "dropdown deve existir").not.toBeNull();
  const viewport = await locator.page().viewportSize();
  expect(viewport).not.toBeNull();
  /* 100% da área útil visível: sem clipping por overflow da tabela. */
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(viewport!.width);
  expect(box!.y + box!.height).toBeLessThanOrEqual(viewport!.height);
}

const SEARCH_LABEL = /Buscar fornecedor por código, razão social ou nome/;

test("tabela V2 — colunas separadas, lupa colapsável e seleção SA2", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-suppliers-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await gotoSheetStep(page);
  await shot("table-empty");

  /* Adicionar cria linha pendente com busca FECHADA — só a lupa. */
  await page
    .getByRole("button", { name: "Adicionar fornecedor" })
    .click();
  const input = page.getByRole("textbox", { name: SEARCH_LABEL });
  await expect(input).toHaveCount(0);
  const lupa = page.getByRole("button", {
    name: "Buscar fornecedor da linha 1",
  });
  await expect(lupa).toBeVisible();
  await expect(lupa).toHaveAttribute("aria-expanded", "false");
  await shot("search-collapsed-lupa-only");

  /* Colunas V2 separadas. Em ≤768px o thead some (cards); desktop
   * valida headers; mobile/tablet validam data-label das células. */
  const table = page.locator(".engineering-prc__supplier-table");
  const cols = [
    "Busca",
    "Código",
    "Loja",
    "Razão social",
    "Nome fantasia",
    "Part Number",
    "Catálogo",
    "Ações",
  ];
  const viewport = page.viewportSize();
  if (viewport && viewport.width > 768) {
    for (const col of cols) {
      await expect(
        table.getByRole("columnheader", { name: col }),
      ).toHaveCount(1);
    }
  } else {
    const firstRow = table.locator("tbody tr").first();
    for (const col of cols) {
      await expect(firstRow.locator(`td[data-label="${col}"]`)).toHaveCount(1);
    }
  }

  /* Lupa abre a área expansível da linha (foco no input SA2). */
  await lupa.click();
  await expect(input).toBeVisible();
  await expect(lupa).toHaveAttribute("aria-expanded", "true");
  await shot("search-open-new-row");

  /* Fechar recolhe; célula Busca volta a exibir só a lupa. */
  await page.getByRole("button", { name: "Fechar busca" }).click();
  await expect(input).toHaveCount(0);
  await expect(lupa).toHaveAttribute("aria-expanded", "false");

  /* Lupa reabre para seleção SA2. */
  await lupa.click();
  await expect(input).toBeVisible();
  await input.fill("0001");
  const listbox = page.getByRole("listbox", {
    name: "Fornecedores sugeridos",
  });
  const firstOption = listbox.getByRole("option").first();
  await expect(firstOption).toBeVisible({ timeout: 15_000 });
  await expectWithinViewport(listbox);
  await shot("dropdown-open");

  /* Seleção preenche Código/Loja/Razão social em colunas próprias e
   * recolhe a busca — nada de concatenação na célula Busca. */
  await firstOption.click();
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await expect(input).toHaveCount(0);
  const firstRow = table.locator("tbody tr").first();
  const codeCell = firstRow.locator('td[data-label="Código"]');
  await expect(codeCell).not.toContainText("—");
  const storeCell = firstRow.locator('td[data-label="Loja"]');
  await expect(storeCell).not.toContainText("—");
  const nameCell = firstRow.locator('td[data-label="Razão social"]');
  await expect(nameCell).not.toContainText("—");
  /* A célula Busca permanece só com a lupa (agora "Alterar"). */
  await expect(
    page.getByRole("button", { name: "Alterar fornecedor da linha 1" }),
  ).toBeVisible();
  await shot("supplier-selected-columns");

  /* Justificativa de inclusão aparece no vínculo novo (create). */
  await expect(
    firstRow.getByRole("button", { name: "Adicionar justificativa opcional" }),
  ).toBeVisible();

  /* PN sem alteração → sem gatilho de justificativa no PN ainda vazio.
   * Preencher PN exibe apenas o gatilho do PN (não o do Catálogo). */
  const pnCell = firstRow.locator('td[data-label="Part Number"]');
  const catCell = firstRow.locator('td[data-label="Catálogo"]');
  await pnCell.locator("input").fill("PN-E2E-1");
  await expect(
    pnCell.getByRole("button", { name: "Adicionar justificativa opcional" }),
  ).toBeVisible();
  await expect(
    catCell.getByRole("button", { name: "Adicionar justificativa opcional" }),
  ).toHaveCount(0);
  await shot("pn-changed-reason-toggle");

  /* Botão compacto — largura do conteúdo, não 100% da coluna. */
  const pnToggle = pnCell.getByRole("button", {
    name: "Adicionar justificativa opcional",
  });
  const toggleBox = await pnToggle.boundingBox();
  const cellBox = await pnCell.boundingBox();
  expect(toggleBox, "gatilho de justificativa deve existir").not.toBeNull();
  expect(cellBox).not.toBeNull();
  expect(toggleBox!.width).toBeLessThan(cellBox!.width * 0.85);
  expect(toggleBox!.height).toBeLessThan(36);

  /* Expandir → textarea ≤250 na linha auxiliar, Recolher preserva. */
  await pnToggle.click();
  const reasonText = page.locator("#prc-sup-pn-reason-0-text");
  await expect(reasonText).toBeVisible();
  await expect(reasonText).toHaveAttribute("maxlength", "250");
  /* 10 chars exactos → contador "10/250 caracteres". */
  await reasonText.fill("motivo-e2e");
  await expect(
    page.locator(".engineering-prc__reason-count", {
      hasText: "10/250 caracteres",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Recolher" }).click();
  await expect(reasonText).toHaveCount(0);
  await shot("reason-editor-open-close");

  /* Limpar o PN esconde o gatilho (desfazer a alteração). */
  await pnCell.locator("input").fill("");
  await expect(
    pnCell.getByRole("button", { name: /justificativa/i }),
  ).toHaveCount(0);

  /* Segunda linha — busca fechada por padrão; lupa abre para razão social. */
  await page
    .getByRole("button", { name: "Adicionar fornecedor" })
    .click();
  const lupa2 = page.getByRole("button", {
    name: "Buscar fornecedor da linha 2",
  });
  await expect(lupa2).toBeVisible();
  await expect(
    page.getByRole("textbox", { name: SEARCH_LABEL }),
  ).toHaveCount(0);
  await lupa2.click();
  const inputs = page.getByRole("textbox", { name: SEARCH_LABEL });
  await inputs.last().fill("TRES RIOS");
  const legalOption = listbox.getByRole("option", {
    name: /BRITAGEM TRES RIOS/,
  });
  await expect(
    legalOption,
    "razão social fora da página 1 deve aparecer",
  ).toBeVisible({ timeout: 15_000 });
  await legalOption.click();
  await expect(
    table.locator('td[data-label="Razão social"]').filter({
      hasText: /BRITAGEM TRES RIOS/,
    }),
  ).toBeVisible();
  await shot("second-supplier-selected");

  /* Escape não deixa painel órfão; remover linha limpa o portal. */
  await page.keyboard.press("Escape");
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Remover fornecedor da linha 2" })
    .click();
  await expect(page.getByRole("listbox")).toHaveCount(0);

  expectNoFailures(forbidden, pageErrors);
});

test("update — diff D13 aciona justificativa só no atributo alterado", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-update-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await page.goto(CREATE_PATH);
  await page
    .getByRole("button", { name: "Alterar produto existente" })
    .click();
  await page.getByLabel(/Código oficial TOTVS/).fill(UPDATE_PRODUCT);
  await page.getByRole("button", { name: "Avançar" }).click();
  await expect(
    page.locator(".engineering-prc__supplier-table"),
  ).toBeVisible({ timeout: 30_000 });
  await shot("update-baseline");

  const table = page.locator(".engineering-prc__supplier-table");
  const firstRow = table.locator("tbody tr").first();
  const pnCell = firstRow.locator('td[data-label="Part Number"]');
  const catCell = firstRow.locator('td[data-label="Catálogo"]');

  /* Vínculo oficial: lupa desabilitada (identidade SA5 não muda). */
  const lupaOfficial = firstRow.getByRole("button", {
    name: /fornecedor da linha 1/,
  });
  await expect(lupaOfficial).toBeDisabled();

  /* Sem alteração → nenhum gatilho de justificativa nas células. */
  await expect(
    pnCell.getByRole("button", { name: /justificativa/i }),
  ).toHaveCount(0);
  await expect(
    catCell.getByRole("button", { name: /justificativa/i }),
  ).toHaveCount(0);

  /* Alterar PN → badge Alterado + valor anterior + gatilho só no PN. */
  const pnInput = pnCell.locator("input");
  const pnBefore = await pnInput.inputValue();
  await pnInput.fill(`${pnBefore}-D14FIX`);
  await expect(pnCell.getByText("Alterado")).toBeVisible();
  await expect(pnCell.getByText(/Anterior:/)).toBeVisible();
  const pnToggle = pnCell.getByRole("button", {
    name: "Adicionar justificativa opcional",
  });
  await expect(pnToggle).toBeVisible();
  await expect(
    catCell.getByRole("button", { name: /justificativa/i }),
  ).toHaveCount(0);
  await shot("update-pn-changed");

  /* Alterar Catálogo → segundo gatilho independente. */
  await catCell.locator("input").fill("CAT-D14FIX");
  await expect(
    catCell.getByRole("button", { name: "Adicionar justificativa opcional" }),
  ).toBeVisible();
  await shot("update-both-changed");

  /* Editor de PN abre na linha auxiliar, não estoura a célula. */
  await pnToggle.click();
  const editor = page.locator(
    ".engineering-prc__supplier-aux #prc-sup-pn-reason-0-text",
  );
  await expect(editor).toBeVisible();
  await editor.fill("ctx pn update");
  await shot("update-pn-reason-editor");
  await page.getByRole("button", { name: "Recolher" }).first().click();

  /* Reverter PN ao baseline → badge e gatilho somem; razão sai do payload. */
  await pnInput.fill(pnBefore);
  await expect(pnCell.getByText("Alterado")).toHaveCount(0);
  await expect(
    pnCell.getByRole("button", { name: /justificativa/i }),
  ).toHaveCount(0);
  await shot("update-pn-reverted");

  /* Remoção proposta → Undo2 + justificativa da operação (na célula
   * Ações — distinta do gatilho de Catálogo ainda alterado). */
  const removeBtn = firstRow.getByRole("button", {
    name: /Solicitar remoção do vínculo/,
  });
  await removeBtn.click();
  await expect(
    firstRow.getByRole("button", { name: /Desfazer remoção/ }),
  ).toBeVisible();
  await expect(firstRow.getByText("Remoção solicitada")).toBeVisible();
  const actionsCell = firstRow.locator('td[data-label="Ações"]');
  await expect(
    actionsCell.getByRole("button", {
      name: "Adicionar justificativa opcional",
    }),
  ).toBeVisible();
  await shot("update-remove-marked");
  await firstRow
    .getByRole("button", { name: /Desfazer remoção/ })
    .click();

  /* Avançar à revisão exige diff: resumo mostra op de Catálogo. */
  await page.getByRole("button", { name: "Avançar" }).click();
  await expect(
    page.getByText(/\(catalogNumber\)/),
  ).toBeVisible();
  await expect(page.getByText(/1 operação/)).toBeVisible();
  await shot("update-review");

  expectNoFailures(forbidden, pageErrors);
});
