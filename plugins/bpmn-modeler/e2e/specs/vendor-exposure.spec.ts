/**
 * WAVE F — VX-*: vendor exposure governance.
 *
 * Prova que capabilities vendor presentes no runtime mas fora do freeze
 * NÃO estão expostas como produto (FUTURE/nao-frozen → not exposed), e que
 * as mantidas permanecem governadas:
 *   - Align/Distribute: FUTURE → sem context pad entry, sem popup, sem action
 *   - Space Tool: não-frozen, muta DI → palette sem entry + 'S' inerte
 *   - Keyboard move selection (setas): move DI → desligado
 *   - Hand Tool: KEEP como implementação de Pan — viewport-only,
 *     nunca canonical/dirty/autosave
 *   - Global Connect: KEEP como alias de Connect — mesmas BpmnRules
 *     (positive + negative deny)
 *   - Engine fields + BPMN-core preserve-only: multiInstance/isExecutable
 *     etc. nunca editáveis
 */
import { test, expect, importModelViaApi, waitSaved } from "../helpers";
import {
  fetchWorkingCopyXml,
  openEditor,
  elBox,
  clickEl,
  deselect,
  selectViaDom,
  focusCanvasSvg,
  shapeIds,
  expectXmlHas,
} from "../ce-helpers";
import {
  PANEL,
  expandAllGroups,
  waitXmlMatch,
} from "../prop-helpers";

const HEADER =
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="Defs_vx" targetNamespace="urn:wavef" exporter="test">';

/**
 * Fixture: processo isExecutable="true" (preservado, edição oculta) +
 * subProcess com multiInstanceLoopCharacteristics (BPMN core
 * preserve-only, nunca engine field) + dois tasks para multi-select e
 * global connect.
 */
const WX_XML =
  HEADER +
  '<bpmn:process id="Process_1" isExecutable="true">' +
  '  <bpmn:startEvent id="S1" name="Início"/>' +
  '  <bpmn:task id="T1" name="Alpha"/>' +
  '  <bpmn:task id="T2" name="Beta"/>' +
  '  <bpmn:subProcess id="SUB1" name="MI Sub">' +
  '    <bpmn:multiInstanceLoopCharacteristics id="MI1" isSequential="true"/>' +
  "  </bpmn:subProcess>" +
  '  <bpmn:endEvent id="E1"/>' +
  '  <bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="Process_1">' +
  '  <bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="80" y="80" width="36" height="36"/></bpmndi:BPMNShape>' +
  '  <bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="200" y="60" width="100" height="80"/></bpmndi:BPMNShape>' +
  '  <bpmndi:BPMNShape id="T2_di" bpmnElement="T2"><dc:Bounds x="380" y="60" width="100" height="80"/></bpmndi:BPMNShape>' +
  '  <bpmndi:BPMNShape id="SUB1_di" bpmnElement="SUB1" isExpanded="true"><dc:Bounds x="180" y="220" width="220" height="140"/></bpmndi:BPMNShape>' +
  '  <bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="560" y="80" width="36" height="36"/></bpmndi:BPMNShape>' +
  '  <bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="116" y="98"/><di:waypoint x="200" y="98"/></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>" +
  "</bpmn:definitions>";

/** Viewport transform do <g> raiz — prova de pan real vs. no-op. */
async function viewportTransform(page: any): Promise<string> {
  return page.evaluate(
    () =>
      document
        .querySelector(".bpmnm-canvas .djs-container > svg > .viewport")
        ?.getAttribute("transform") ?? "",
  );
}

/** Sleep curto > debounce do autosave (1.5s) para assert de não-mutação. */
const AUTOSAVE_DRAIN_MS = 2_400;

/**
 * Comparação semântica de canonical XML — o primeiro write de um modelo
 * importado re-serializa via moddle (`<tag />` → `<tag/>`, whitespace
 * entre children). Normaliza o formato sem tolerar mudança de conteúdo.
 */
function normalizeXml(xml: string): string {
  return xml.replace(/\s*\/>/g, "/>").replace(/>\s+</g, "><").trim();
}

function connectionCount(page: any): Promise<number> {
  return page.evaluate(
    () => document.querySelectorAll(".djs-element.djs-connection").length,
  );
}

test.describe("WAVE F — vendor exposure governance", () => {
  test.use({ actor: "editor" });

  test("VX-01: multi-select não expõe align/distribute; palette sem space-tool", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "VX-01", WX_XML);
    await openEditor(page, modelId);

    // palette: space-tool removida; tools IN_V1 presentes
    const palette = page.locator(".djs-palette");
    await expect(
      palette.locator('.entry[data-action="space-tool"]'),
    ).toHaveCount(0);
    await expect(
      palette.locator('.entry[data-action="lasso-tool"]'),
    ).toBeVisible();
    await expect(
      palette.locator('.entry[data-action="hand-tool"]'),
    ).toBeVisible();
    await expect(
      palette.locator('.entry[data-action="global-connect-tool"]'),
    ).toBeVisible();

    // multi-select real (T1+T2) → context pad sem 'align-elements'
    await selectViaDom(page, "T1");
    await selectViaDom(page, "T2", true);
    const pad = page.locator(".djs-context-pad.open");
    await expect(pad).toBeVisible({ timeout: 10_000 });
    await expect(
      pad.locator('.entry[data-action="align-elements"]'),
    ).toHaveCount(0);
    // nenhum popup align-elements aberto ou acessível
    await expect(page.locator(".djs-popup.align-elements")).toHaveCount(0);
  });

  test("VX-02: 'S' não ativa space tool — drag não muta canonical/DI/dirty", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "VX-02", WX_XML);
    await openEditor(page, modelId);
    const before = await fetchWorkingCopyXml("editor", modelId);

    await focusCanvasSvg(page);
    await page.keyboard.press("s");
    // drag em área vazia do canvas — com space-tool ativo, abriria espaço
    // horizontal empurrando elementos (mutação DI); inerte = no-op
    const box = await page
      .locator(".bpmnm-canvas .djs-container")
      .boundingBox();
    const x0 = box!.x + box!.width * 0.55;
    const y0 = box!.y + box!.height * 0.85;
    await page.mouse.move(x0, y0);
    await page.mouse.down();
    await page.mouse.move(x0 + 180, y0, { steps: 10 });
    await page.mouse.up();

    await page.waitForTimeout(AUTOSAVE_DRAIN_MS);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
    expect(
      normalizeXml(await fetchWorkingCopyXml("editor", modelId)),
    ).toBe(normalizeXml(before));
  });

  test("VX-03: setas não movem a seleção (keyboard move desligado)", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "VX-03", WX_XML);
    await openEditor(page, modelId);
    const before = await fetchWorkingCopyXml("editor", modelId);

    await selectViaDom(page, "T1");
    await focusCanvasSvg(page);
    for (const key of ["ArrowRight", "ArrowRight", "ArrowUp"]) {
      await page.keyboard.press(key);
    }

    await page.waitForTimeout(AUTOSAVE_DRAIN_MS);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
    expect(
      normalizeXml(await fetchWorkingCopyXml("editor", modelId)),
    ).toBe(normalizeXml(before));
  });

  test("VX-04: Hand tool pan — viewport muda, canonical/DI/dirty intactos", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "VX-04", WX_XML);
    await openEditor(page, modelId);
    const before = await fetchWorkingCopyXml("editor", modelId);
    const transformBefore = await viewportTransform(page);

    await focusCanvasSvg(page);
    await page.keyboard.press("h"); // hand tool ON (KEEP — Pan impl)
    await deselect(page);
    const box = await page
      .locator(".bpmnm-canvas .djs-container")
      .boundingBox();
    const cx = box!.x + box!.width / 2;
    const cy = box!.y + box!.height / 2;
    await page.mouse.move(cx, cy);
    await page.mouse.down();
    await page.mouse.move(cx + 160, cy + 90, { steps: 8 });
    await page.mouse.up();

    await expect
      .poll(() => viewportTransform(page))
      .not.toBe(transformBefore);
    await page.waitForTimeout(AUTOSAVE_DRAIN_MS);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
    expect(
      normalizeXml(await fetchWorkingCopyXml("editor", modelId)),
    ).toBe(normalizeXml(before));
  });

  test("VX-05: Global Connect governado — connect permitido persiste e undo reverte", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "VX-05", WX_XML);
    await openEditor(page, modelId);

    await focusCanvasSvg(page);
    await deselect(page);
    await page.keyboard.press("c"); // global connect ON
    const t1 = await elBox(page, "T1");
    const t2 = await elBox(page, "T2");
    await page.mouse.move(t1.x + t1.width / 2, t1.y + t1.height / 2);
    await page.mouse.down();
    await page.mouse.move(t2.x + t2.width / 2, t2.y + t2.height / 2, {
      steps: 10,
    });
    await page.mouse.up();

    // conexão criada via rules → sequenceFlow T1→T2 no canonical
    await waitXmlMatch(
      "editor",
      modelId,
      /<bpmn:sequenceFlow[^>]*sourceRef="T1"[^>]*targetRef="T2"/,
    );

    // undo/remove pelo command stack
    await focusCanvasSvg(page);
    await page.keyboard.press("Control+z");
    await waitXmlMatch(
      "editor",
      modelId,
      /sourceRef="T1"[^>]*targetRef="T2"/,
      false,
    );
  });

  test("VX-06: Global Connect respeita rules — rota proibida (→start) negada", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "VX-06", WX_XML);
    await openEditor(page, modelId);
    const before = await fetchWorkingCopyXml("editor", modelId);
    const connBefore = await connectionCount(page);

    await focusCanvasSvg(page);
    await deselect(page);
    await page.keyboard.press("c");
    const t2 = await elBox(page, "T2");
    const s1 = await elBox(page, "S1");
    await page.mouse.move(t2.x + t2.width / 2, t2.y + t2.height / 2);
    await page.mouse.down();
    await page.mouse.move(s1.x + s1.width / 2, s1.y + s1.height / 2, {
      steps: 10,
    });
    await page.mouse.up();

    // startEvent não aceita incoming sequenceFlow; mesmo participant
    // nega messageFlow; alvo não é artifact → association negada
    expect(await connectionCount(page)).toBe(connBefore);
    await page.waitForTimeout(AUTOSAVE_DRAIN_MS);
    await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo");
    expect(
      normalizeXml(await fetchWorkingCopyXml("editor", modelId)),
    ).toBe(normalizeXml(before));
  });

  test("VX-07: painel sem engine fields e sem grupos preserve-only", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "VX-07", WX_XML);
    await openEditor(page, modelId);

    const DENY_ENTRIES = [
      "isExecutable",
      "versionTag",
      "candidateUsers",
      "candidateGroups",
      "calledElementBinding",
      "calledElementVersion",
      "calledElementVersionTag",
      "calledElementTenantId",
      "multiInstance",
      "asyncBefore",
      "asyncAfter",
      "jobPriority",
      "retryTimeCycle",
      "executionListeners",
      "taskListeners",
      "delegateExpression",
      "class",
      "expression",
    ];

    async function assertCleanPanel(elementId: string) {
      await clickEl(page, elementId);
      await expandAllGroups(page);
      const entryIds = await page
        .locator(`${PANEL} [data-entry-id]`)
        .evaluateAll((ns) =>
          ns.map((n) => n.getAttribute("data-entry-id") ?? ""),
        );
      const groupIds = await page
        .locator(`${PANEL} [data-group-id]`)
        .evaluateAll((ns) =>
          ns.map((n) => n.getAttribute("data-group-id") ?? ""),
        );
      for (const id of entryIds.concat(groupIds)) {
        const base = id.replace(/^group-/, "");
        expect(
          DENY_ENTRIES.includes(base),
          `surface não classificada exposta: ${id}`,
        ).toBe(false);
      }
    }

    await assertCleanPanel("T1");
    await assertCleanPanel("SUB1"); // MI preserve-only: sem grupo multiInstance

    // root (processo) — isExecutable hidden by product decision
    await deselect(page);
    await expandAllGroups(page);
    const rootEntries = await page
      .locator(`${PANEL} [data-entry-id]`)
      .evaluateAll((ns) =>
        ns.map((n) => n.getAttribute("data-entry-id") ?? ""),
      );
    expect(rootEntries).not.toContain("isExecutable");
    expect(rootEntries).not.toContain("versionTag");
  });

  test("VX-08: BPMN core preserve-only preservado no round-trip (MI + isExecutable)", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "VX-08", WX_XML);
    await openEditor(page, modelId);

    const xml = await fetchWorkingCopyXml("editor", modelId);
    expectXmlHas(
      xml,
      /<bpmn:multiInstanceLoopCharacteristics/,
      "MI preservado (BPMN core, não engine field)",
    );
    expectXmlHas(xml, /isExecutable="true"/, "isExecutable preservado");

    await page.reload();
    await expect(
      page.locator(".bpmnm-canvas .djs-container"),
    ).toBeVisible({ timeout: 20_000 });
    await waitSaved(page);
    const after = await fetchWorkingCopyXml("editor", modelId);
    expectXmlHas(after, /<bpmn:multiInstanceLoopCharacteristics/, "MI pós-reload");
    expectXmlHas(after, /isExecutable="true"/, "isExecutable pós-reload");
    expect(await shapeIds(page)).toContain("SUB1");
  });
});
