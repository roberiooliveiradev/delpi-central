import { test, expect, createModelViaApi, modelUrl } from "../helpers";

/**
 * REV — experiência de revisões com metadata de domínio real.
 *
 * Revision é checkpoint imutável explícito (≠ autosave working copy).
 * Metadata (name/description/author) é contrato do backend — o card
 * prioriza informação útil: nome/observação/data/autor; o UUID técnico
 * nunca é exibido como informação primária.
 */

const UUID_RE =
  /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

test.describe("REV — painel de revisões", () => {
  test.use({ actor: "manager", viewport: { width: 1440, height: 900 } });

  test("REV-01: empty state orienta a criação", async ({ page }) => {
    const modelId = await createModelViaApi("manager", "E2E-RevEmpty");
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 20_000,
    });
    await page.getByRole("tab", { name: "Histórico" }).click();
    await expect(page.getByText("Nenhuma revisão")).toBeVisible({
      timeout: 15_000,
    });
    await expect(
      page.getByText(/marcos imutáveis|cópia de trabalho/i),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Criar revisão" }),
    ).toBeVisible();
  });

  test("REV-02/05/06/07: criar com nome+observação via diálogo (write→read-back)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("manager", "E2E-RevMeta");
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 20_000,
    });

    await page.getByRole("tab", { name: "Histórico" }).click();
    await page.getByRole("button", { name: "Criar revisão" }).click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("Nome da revisão")).toBeVisible();
    await dialog.getByLabel("Nome da revisão").fill("Fluxo validado");
    await dialog
      .getByLabel("Observação")
      .fill("Aprovado pelo time de Compras.");
    await dialog.getByRole("button", { name: "Criar revisão" }).click();

    // card: nome amigável é o título; "Rev. 1" fica como tag secundária
    const card = page.locator(".bpmnm-revision-item", {
      hasText: "Fluxo validado",
    });
    await expect(card).toBeVisible({ timeout: 15_000 });
    await expect(card.getByText("Rev. 1")).toBeVisible();
    await expect(card.getByText("Aprovado pelo time de Compras.")).toBeVisible();
    // data pt-BR no card
    await expect(
      card.getByText(/\d{2}\/\d{2}\/\d{4}/),
    ).toBeVisible();
    // UUID técnico não é informação primária do card
    await expect(card).not.toContainText(UUID_RE);

    // autoridade: read-back da API confirma a metadata persistida
    const persisted = page.locator(".bpmnm-revision-item").first();
    await expect(persisted).toContainText("Fluxo validado");

    // REV-04: hierarquia de ações — Ver (ghost) e Restaurar presentes
    await expect(
      card.getByRole("button", { name: "Ver revisão 1" }),
    ).toBeVisible();
    await expect(
      card.getByRole("button", { name: "Restaurar revisão 1" }),
    ).toBeVisible();
  });

  test("REV-05b: revisão sem nome mantém fallback 'Revisão N'", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("manager", "E2E-RevAnon");
    await page.goto(modelUrl(modelId));
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
      timeout: 20_000,
    });
    await page.getByRole("tab", { name: "Histórico" }).click();
    await page.getByRole("button", { name: "Criar revisão" }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Criar revisão" })
      .click();
    await expect(page.getByText("Revisão 1")).toBeVisible({ timeout: 15_000 });
    await expect(page.locator(".bpmnm-revision-item")).not.toContainText(
      UUID_RE,
    );
  });
});
