import { expect, test, type Page } from "@playwright/test";

import { loginAsDev } from "../helpers";

/** PRC-UX-CHANGE-01 — visualização das alterações solicitadas no
 * detalhe UPDATE. Usa o caso real DEV `914350dc…` (código oficial
 * 10080025, única alteração: description). Credenciais do analista
 * via env (DEV_PORTAL_USERNAME/PASSWORD). */

const UPDATE_CASE = "914350dc-2c7a-466a-8e22-cd657b0f9c40";
const DETAIL_URL = `/apps/engineering/product-registration/${UPDATE_CASE}`;

async function openDetail(page: Page) {
  await loginAsDev(page);
  await page.goto(DETAIL_URL);
  await expect(
    page.getByText("Identificação do produto"),
  ).toBeVisible({ timeout: 60_000 });
}

test.describe("PRC-UX-CHANGE-01 — detalhe UPDATE", () => {
  test("apenas alterações solicitadas, sem duplicação nem objeto bruto", async ({
    page,
  }, testInfo) => {
    await openDetail(page);

    // Identificação + código oficial sempre visíveis.
    await expect(page.getByText("Identificação do produto")).toBeVisible();
    await expect(page.getByText("10080025").first()).toBeVisible();

    // Card de alterações com comparação.
    await expect(page.getByText("Alterações solicitadas")).toBeVisible();
    await expect(
      page.getByText("Antes", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      page.getByText("Solicitado", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      page.getByText(/TERM\. OLHAL M6.*TESTE/).first(),
    ).toBeVisible();

    // Sem [object Object] em nenhum lugar.
    await expect(page.getByText(/\[object Object\]/)).toHaveCount(0);

    // Sem card de fornecedores (nenhuma operação solicitada).
    await expect(
      page.getByText("Nenhum fornecedor vinculado."),
    ).toHaveCount(0);
    await expect(page.getByText("Fornecedores")).toHaveCount(0);

    // Sem card de documentos vazio (caso sem anexos).
    await expect(page.getByText("Documentos de apoio")).toHaveCount(0);

    // Sem ficha completa: grupos genéricos não renderizam.
    await expect(page.getByText("Estoque e contabilidade")).toHaveCount(0);

    await page.screenshot({
      path: `e2e/artifacts/prc-ux-change-01-update-${testInfo.project.name}.png`,
      fullPage: true,
    });
  });
});
