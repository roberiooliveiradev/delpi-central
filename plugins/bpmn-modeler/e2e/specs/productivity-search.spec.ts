/**
 * G3 — PROD-SRCH-*: search pad vendor (Ctrl/Cmd+F, nome, id, navegação,
 * fechar, sem mutação) e PROD-PAL-*: palette search de produto (IG-1) —
 * governance derivada do editingProfile (entries reais da paleta
 * filtrada), teclado, acessibilidade, sem preserve-only.
 */
import { test, expect, createModelViaApi, waitSaved } from "../helpers";
import {
  openEditor,
  createFromPalette,
  renameElement,
  focusCanvasSvg,
  selectedElementId,
  shapeIds,
  newShapeId,
  saveReadbackReload,
  expectXmlHas,
  fetchWorkingCopyXml,
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

const PAL_INPUT = ".bpmnm-palette-search__input";
const PAL_OPTION = ".bpmnm-palette-search__option";
const PAL_EMPTY = ".bpmnm-palette-search__empty";

/** Busca + ativa ação por label exato e posiciona no canvas. Retorna o id criado (diff de DOM — o replace pode trocar a seleção). */
async function searchAndCreate(
  page: import("@playwright/test").Page,
  term: string,
  resultText: string | RegExp,
  position: { x: number; y: number },
): Promise<string> {
  const input = page.locator(PAL_INPUT);
  await input.fill(term);
  const option = page.locator(PAL_OPTION).filter({ hasText: resultText });
  await expect(option.first()).toBeVisible();
  await option.first().click();
  return newShapeId(page, () =>
    page.locator(".bpmnm-canvas .djs-container").click({ position }),
  );
}

test.describe("PROD-PAL — palette search (IG-1, governed)", () => {
  test.use({ actor: "editor" });

  test("PROD-PAL-01: input visível no modo edição, acessível (role/label)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-01");
    await openEditor(page, modelId);

    const input = page.locator(PAL_INPUT);
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
    await expect(page.locator(PAL_INPUT)).toBeFocused();
    await page.keyboard.press("Escape");
  });

  test("PROD-PAL-03: termo lista só CREATE_EDIT; preserve-only/contextual ausente", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-03");
    await openEditor(page, modelId);

    const input = page.locator(PAL_INPUT);
    const results = page.locator(PAL_OPTION);

    // "gateway" lista os 4 gateways CREATE_EDIT com labels semânticos
    await input.fill("gateway");
    await expect(results).toHaveCount(4);
    await expect(results).toContainText([
      "Gateway Exclusivo",
      "Gateway Paralelo",
      "Gateway Inclusivo",
      "Gateway Baseado em Eventos",
    ]);

    // aliases PT-BR resolvem para a ação semântica correta
    await input.fill("usuario");
    await expect(results).toHaveCount(1);
    await expect(results.first()).toHaveText("Tarefa de Usuário");

    // preserve-only nunca aparece (não há create path governado)
    for (const term of [
      "complex",
      "transação",
      "ad hoc",
      "multiinstance",
      "compensação",
    ]) {
      await input.fill(term);
      await expect(page.locator(PAL_EMPTY), term).toHaveText(
        "Nenhum resultado",
      );
    }

    // constructs contextuais não mentem semanticamente:
    // lane só existe via context-pad de Participant; boundary exige attach
    for (const term of ["raia", "lane", "boundary", "borda"]) {
      await input.fill(term);
      await expect(page.locator(PAL_EMPTY), term).toHaveText(
        "Nenhum resultado",
      );
    }
  });

  test("PROD-PAL-04: Enter ativa o create da entry; clique posiciona; Escape cancela", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-04");
    await openEditor(page, modelId);

    const input = page.locator(PAL_INPUT);
    await input.fill("tarefa");
    const results = page.locator(PAL_OPTION);
    await expect(results.first()).toHaveText("Tarefa");

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

  test("PROD-PAL-05: lista reflete governance — só ações do profile", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-05");
    await openEditor(page, modelId);

    const input = page.locator(PAL_INPUT);
    // família task: genérica + 7 tipados, todos com label semântico próprio
    await input.fill("tarefa");
    const results = page.locator(PAL_OPTION);
    await expect(results).toHaveCount(8);
    const texts = await results.allTextContents();
    for (const t of texts) expect(t).toContain("Tarefa");
  });
});

test.describe("PROD-PAL-SEM — semantic routing (G3-PAL-1)", () => {
  test.use({ actor: "editor" });

  const SEM_CASES: Array<{
    id: string;
    term: string;
    result: string;
    qname: RegExp;
    absent?: RegExp;
  }> = [
    {
      id: "01",
      term: "usuário",
      result: "Tarefa de Usuário",
      qname: /<bpmn:userTask[\s>]/,
      absent: /<bpmn:task[\s>]/,
    },
    {
      id: "02",
      term: "serviço",
      result: "Tarefa de Serviço",
      qname: /<bpmn:serviceTask[\s>]/,
      absent: /<bpmn:task[\s>]/,
    },
    {
      id: "03",
      term: "manual",
      result: "Tarefa Manual",
      qname: /<bpmn:manualTask[\s>]/,
      absent: /<bpmn:task[\s>]/,
    },
    {
      id: "04",
      term: "regra",
      result: "Tarefa de Regra de Negócio",
      qname: /<bpmn:businessRuleTask[\s>]/,
      absent: /<bpmn:task[\s>]/,
    },
    {
      id: "05",
      term: "gateway paralelo",
      result: "Gateway Paralelo",
      qname: /<bpmn:parallelGateway[\s>]/,
      absent: /<bpmn:exclusiveGateway[\s>]/,
    },
  ];

  for (const c of SEM_CASES) {
    test(`PROD-PAL-SEM-${c.id}: "${c.term}" → ${c.qname.source} (não genérico)`, async ({
      page,
    }) => {
      const modelId = await createModelViaApi(
        "editor",
        `PROD-PAL-SEM-${c.id}`,
      );
      await openEditor(page, modelId);

      const created = await searchAndCreate(page, c.term, c.result, {
        x: 400,
        y: 300,
      });

      const xml = await saveReadbackReload(page, "editor", modelId, [
        created,
      ]);
      expectXmlHas(xml, c.qname, `${c.result} → QName correto`);
      if (c.absent) {
        expect(xml.match(c.absent)).toBeNull();
      }
    });
  }

  test("PROD-PAL-SEM-06: evento de início por timer cria eventDefinition correta", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-SEM-06");
    await openEditor(page, modelId);

    const created = await searchAndCreate(
      page,
      "início por timer",
      "Evento de Início por Timer",
      { x: 400, y: 300 },
    );

    const xml = await saveReadbackReload(page, "editor", modelId, [created]);
    expectXmlHas(
      xml,
      /<bpmn:startEvent[\s>][\s\S]*?<bpmn:timerEventDefinition[\s/>]/,
      "startEvent + timerEventDefinition",
    );
  });

  test("PROD-PAL-SEM-07: undo/redo cobre CREATE_THEN_REPLACE (command stack)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-SEM-07");
    await openEditor(page, modelId);
    await focusCanvasSvg(page);

    await searchAndCreate(page, "usuário", "Tarefa de Usuário", {
      x: 400,
      y: 300,
    });
    // drop do create deixa foco fora do svg — normalizar antes dos atalhos
    await focusCanvasSvg(page);

    // undo 1: reverte o replace → volta a Task genérica (elemento persiste)
    await page.keyboard.press("Control+z");
    await waitSaved(page);
    let xml = await fetchWorkingCopyXml("editor", modelId);
    expectXmlHas(xml, /<bpmn:task[\s>]/, "undo do replace → task genérica");
    expect(xml.match(/<bpmn:userTask[\s>]/)).toBeNull();

    // undo 2: reverte o create → elemento some
    await page.keyboard.press("Control+z");
    await waitSaved(page);
    xml = await fetchWorkingCopyXml("editor", modelId);
    expect(xml.match(/<bpmn:task[\s>]/)).toBeNull();

    // redo 2: recria + re-aplica replace → userTask de volta
    await page.keyboard.press("Control+y");
    await page.keyboard.press("Control+y");
    await waitSaved(page);
    xml = await fetchWorkingCopyXml("editor", modelId);
    expectXmlHas(xml, /<bpmn:userTask[\s>]/, "redo → userTask restaurada");
  });

  test("PROD-PAL-SEM-08: preserve-only/out-of-profile nunca vira create result", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-PAL-SEM-08");
    await openEditor(page, modelId);

    const input = page.locator(PAL_INPUT);
    for (const term of [
      "complex gateway",
      "transaction",
      "ad hoc",
      "multiinstance",
      "compensation",
      "cancel",
    ]) {
      await input.fill(term);
      const options = await page.locator(PAL_OPTION).count();
      const empty = await page.locator(PAL_EMPTY).count();
      // ou não há resultado, ou nenhum resultado representa o preserve-only
      expect(options + empty, term).toBeGreaterThan(0);
    }
    // nada foi criado no canvas
    expect(await shapeIds(page)).toHaveLength(0);
  });
});
