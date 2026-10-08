/**
 * G3 — PROD-SRCH-*: search pad vendor (Ctrl/Cmd+F, nome, id, navegação,
 * fechar, sem mutação) e PROD-PAL-*: palette search de produto (IG-1) —
 * governance derivada do editingProfile (entries reais da paleta
 * filtrada), teclado, acessibilidade, sem preserve-only.
 */
import { test, expect, createModelViaApi } from "../helpers";
import {
  openEditor,
  createFromPalette,
  renameElement,
  focusCanvasSvg,
  selectedElementId,
  shapeIds,
  saveReadbackReload,
  expectXmlHas,
} from "../ce-helpers";

const SEARCH = ".djs-search-container";
const SEARCH_INPUT = ".djs-search-input input";
const RESULT = ".djs-search-result";

test.describe("PROD-SRCH — Ctrl+F search pad", () => {
  test.use({ actor: "editor" });

  test("PROD-SRCH-01: Ctrl+F abre, busca por nome seleciona, Escape fecha", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SRCH-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.task", 480, 200);
    const b = await selectedElementId(page);
    await renameElement(page, a, "Aprovar Pedido");
    await renameElement(page, b, "Analisar Credito");

    // Ctrl+F abre o search pad (svg focado — keyboard vendor é bound a ele)
    await focusCanvasSvg(page);
    await page.keyboard.press("Control+f");
    const pad = page.locator(SEARCH);
    await expect(pad).toBeVisible();
    const input = page.locator(SEARCH_INPUT);
    await expect(input).toBeFocused();

    // busca por nome (parcial) — o vendor pesquisa no keyup do input,
    // então digitação real é obrigatória (fill() não dispara keyup)
    await input.pressSequentially("Pedido");
    await expect(page.locator(RESULT)).toHaveCount(1);
    await expect(page.locator(RESULT).first()).toContainText("Aprovar Pedido");

    // Enter seleciona o resultado atual
    await page.keyboard.press("Enter");
    await expect(
      page.locator(`.djs-element.selected[data-element-id="${a}"]`),
    ).toBeAttached();

    // Escape fecha sem mutação
    const shapesBefore = (await shapeIds(page)).length;
    await focusCanvasSvg(page);
    await page.keyboard.press("Control+f");
    await page.locator(SEARCH_INPUT).pressSequentially("x");
    await page.keyboard.press("Escape");
    await expect(page.locator(SEARCH)).not.toBeVisible();
    expect((await shapeIds(page)).length).toBe(shapesBefore);
  });

  test("PROD-SRCH-02: busca por id navega até o elemento", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SRCH-02");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.end-event", 460, 200);
    const end = await selectedElementId(page);

    await focusCanvasSvg(page);
    await page.keyboard.press("Control+f");
    const input = page.locator(SEARCH_INPUT);
    await input.pressSequentially(end);
    await expect(page.locator(RESULT)).toHaveCount(1);
    await expect(page.locator(RESULT).first()).toContainText(end);
    await page.keyboard.press("Enter");
    await expect(
      page.locator(`.djs-element.selected[data-element-id="${end}"]`),
    ).toBeAttached();
  });

  test("PROD-SRCH-03: nomes quase duplicados → 2 matches, navegação seleciona", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SRCH-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.task", 480, 200);
    const b = await selectedElementId(page);
    await createFromPalette(page, "create.task", 200, 420);
    const c = await selectedElementId(page);
    await renameElement(page, a, "Revisao Orcamento Norte");
    await renameElement(page, b, "Revisao Orcamento Sul");
    await renameElement(page, c, "Faturamento");

    await focusCanvasSvg(page);
    await page.keyboard.press("Control+f");
    const input = page.locator(SEARCH_INPUT);
    await input.pressSequentially("Revisao Orcamento");
    await expect(page.locator(RESULT)).toHaveCount(2);

    // ArrowDown navega entre matches; Enter seleciona o corrente
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
    const sel = await page.locator(".djs-element.selected").count();
    expect(sel).toBeGreaterThanOrEqual(1);
  });

  test("PROD-SRCH-04: busca com acento funciona (substring)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SRCH-04");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await renameElement(page, a, "Validar Orçamento Anual");

    await focusCanvasSvg(page);
    await page.keyboard.press("Control+f");
    await page.locator(SEARCH_INPUT).pressSequentially("Orçamento");
    await expect(page.locator(RESULT)).toHaveCount(1);
    await expect(page.locator(RESULT).first()).toContainText(
      "Orçamento",
    );
  });
});

test.describe("PROD-PAL — palette search (IG-1, governed)", () => {
  test.use({ actor: "editor" });

  test("PROD-PAL-01: input visível no modo edição, acessível (role/label)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-01");
    await openEditor(page, modelId);

    const input = page.locator(".bpmnm-palette-search__input");
    await expect(input).toBeVisible();
    await expect(input).toHaveAttribute("role", "combobox");
    await expect(input).toHaveAttribute("aria-label", "Buscar na paleta");
  });

  test("PROD-PAL-02: '/' abre/foca a busca via teclado", async ({ page }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-02");
    await openEditor(page, modelId);

    // foco fora de campo de texto → '/' foca o input
    await page.locator(".bpmnm-canvas .djs-container").click({
      position: { x: 400, y: 300 },
    });
    await page.keyboard.press("/");
    await expect(
      page.locator(".bpmnm-palette-search__input"),
    ).toBeFocused();
    await page.keyboard.press("Escape");
  });

  test("PROD-PAL-03: termo lista só CREATE_EDIT; preserve-only ausente", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-03");
    await openEditor(page, modelId);

    const input = page.locator(".bpmnm-palette-search__input");
    await input.fill("gateway");
    const results = page.locator(".bpmnm-palette-search__option");
    await expect(results).toHaveCount(1);
    await expect(results.first()).toContainText("Criar gateway");

    // aliases PT-BR resolvem para entries governadas
    await input.fill("usuario");
    await expect(results).toHaveCount(1);
    await expect(results.first()).toContainText("Criar tarefa");

    // preserve-only nunca aparece (não há entry governada para eles)
    await input.fill("complex");
    await expect(
      page.locator(".bpmnm-palette-search__empty"),
    ).toHaveText("Nenhum resultado");
    await input.fill("transação");
    await expect(
      page.locator(".bpmnm-palette-search__empty"),
    ).toHaveText("Nenhum resultado");
    await input.fill("ad hoc");
    await expect(
      page.locator(".bpmnm-palette-search__empty"),
    ).toHaveText("Nenhum resultado");
  });

  test("PROD-PAL-04: Enter ativa o create da entry; clique posiciona; Escape cancela", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-04");
    await openEditor(page, modelId);

    const input = page.locator(".bpmnm-palette-search__input");
    await input.fill("tarefa");
    const results = page.locator(".bpmnm-palette-search__option");
    await expect(results.first()).toContainText("Criar tarefa");

    // navegação por teclado + Enter entra na interação de create do vendor
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowUp");
    await page.keyboard.press("Enter");

    // cursor carrega o preview do create → clique no canvas posiciona
    await page.locator(".bpmnm-canvas .djs-container").click({
      position: { x: 300, y: 260 },
    });
    const created = await selectedElementId(page);

    // input limpo/fechado após ativação
    await expect(input).toHaveValue("");

    const xml = await saveReadbackReload(page, "editor", modelId, [created]);
    expectXmlHas(xml, /<bpmn:task[\s>]/, "task criada via palette search");
  });

  test("PROD-PAL-05: lista reflete governance — sem entries fora do profile", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-05");
    await openEditor(page, modelId);

    const input = page.locator(".bpmnm-palette-search__input");
    // termo amplo: todos os resultados devem ser entries create.* visíveis
    // na própria paleta (a fonte é palette.getEntries() filtrada)
    await input.fill("criar");
    const results = page.locator(".bpmnm-palette-search__option");
    const count = await results.count();
    expect(count).toBeGreaterThanOrEqual(5);
    // cada resultado corresponde a uma entry real da paleta vendor
    const paletteEntries = await page
      .locator(".djs-palette .entry[data-action^='create.']")
      .count();
    expect(count).toBeLessThanOrEqual(paletteEntries);
  });
});
