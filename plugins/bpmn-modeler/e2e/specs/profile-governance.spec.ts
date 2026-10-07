/**
 * GOV (E2E) — BPMN editing profile governance (G2A).
 *
 * Prova no produto real (stack completa) que as surfaces de criação do
 * vendor respeitam o profile V1: constructs RENDER_PRESERVE_ONLY e fora
 * do profile não são criáveis nem aparecem como replace target, enquanto
 * CREATE_EDIT continua funcional e o canônico preserva imports.
 *
 * Evidência: palette entries, context pad append, replace popup entries +
 * header toggles, properties panel groups, e preservação de fixture
 * preserve-only por autosave → read-back.
 */
import {
  test,
  expect,
  importModelViaApi,
  modelUrl,
  waitSaved,
} from "../helpers";

const BPMN_HEAD =
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="Definitions_gov" targetNamespace="urn:gov" ' +
  'exporter="test" exporterVersion="1.0">\n';
const BPMN_TAIL = "</bpmn:definitions>";

/** Fixture com constructs preserve-only + in-profile misturados. */
const XML_PRESERVE_ONLY =
  BPMN_HEAD +
  '  <bpmn:process id="P1" isExecutable="false">' +
  '    <bpmn:startEvent id="S1"/>' +
  '    <bpmn:task id="T1"/>' +
  '    <bpmn:eventBasedGateway id="EG1"/>' +
  '    <bpmn:complexGateway id="CG1"/>' +
  '    <bpmn:transaction id="TR1"><bpmn:task id="TT1"/></bpmn:transaction>' +
  '    <bpmn:adHocSubProcess id="AH1"><bpmn:task id="AT1"/></bpmn:adHocSubProcess>' +
  '    <bpmn:intermediateCatchEvent id="C1">' +
  '      <bpmn:conditionalEventDefinition id="CED1"/>' +
  "    </bpmn:intermediateCatchEvent>" +
  '    <bpmn:boundaryEvent id="B1" attachedToRef="T1" cancelActivity="false">' +
  '      <bpmn:errorEventDefinition id="ED1"/>' +
  "    </bpmn:boundaryEvent>" +
  "  </bpmn:process>" +
  '  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '    <bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="40" y="80" width="36" height="36"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="160" y="60" width="100" height="80"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="EG1_di" bpmnElement="EG1"><dc:Bounds x="320" y="60" width="50" height="50"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="CG1_di" bpmnElement="CG1"><dc:Bounds x="420" y="60" width="50" height="50"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="TR1_di" bpmnElement="TR1"><dc:Bounds x="100" y="220" width="240" height="160"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="AH1_di" bpmnElement="AH1"><dc:Bounds x="400" y="220" width="240" height="160"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="C1_di" bpmnElement="C1"><dc:Bounds x="520" y="60" width="36" height="36"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="B1_di" bpmnElement="B1"><dc:Bounds x="180" y="122" width="36" height="36"/></bpmndi:BPMNShape>' +
  "  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n" +
  BPMN_TAIL;

async function openEditor(page: import("@playwright/test").Page, modelId: string) {
  await page.goto(modelUrl(modelId));
  await expect(page.locator(".bpmnm-canvas .djs-container")).toBeVisible({
    timeout: 20_000,
  });
  await waitSaved(page);
}

async function selectElement(
  page: import("@playwright/test").Page,
  id: string,
) {
  await page
    .locator(`.djs-element[data-element-id="${id}"]`)
    .click({ position: { x: 8, y: 8 }, force: true });
}

test.describe("GOV — palette governance", () => {
  test.use({ actor: "editor" });

  test("GOV-PAL: palette não expõe criação fora do profile", async ({
    page,
  }) => {
    const modelId = await importModelViaApi(
      "editor",
      "GOV Palette",
      XML_PRESERVE_ONLY,
    );
    await openEditor(page, modelId);

    const actions = await page.evaluate(() =>
      [...document.querySelectorAll(".djs-palette .entry")].map((e) =>
        e.getAttribute("data-action"),
      ),
    );
    expect(actions.length).toBeGreaterThan(0);
    for (const action of actions) {
      expect(action).not.toContain("transaction");
      expect(action).not.toContain("complex");
      expect(action).not.toContain("ad-hoc");
      expect(action).not.toContain("event-subprocess");
    }
    // in-profile create entries continuam disponíveis
    for (const action of [
      "create.task",
      "create.start-event",
      "create.exclusive-gateway",
      "create.participant-expanded",
      "create.group",
    ]) {
      expect(actions, `palette entry ${action} ausente`).toContain(action);
    }
  });
});

test.describe("GOV — context pad governance", () => {
  test.use({ actor: "editor" });

  test("GOV-PAD: EventBasedGateway não oferece conditional catch append", async ({
    page,
  }) => {
    const modelId = await importModelViaApi(
      "editor",
      "GOV ContextPad",
      XML_PRESERVE_ONLY,
    );
    await openEditor(page, modelId);
    await selectElement(page, "EG1");

    const pad = page.locator(".djs-context-pad.open");
    await expect(pad).toBeVisible({ timeout: 10_000 });

    const entries = await page.evaluate(() =>
      [...document.querySelectorAll(".djs-context-pad.open .entry")].map((e) =>
        e.getAttribute("data-action"),
      ),
    );
    expect(entries).not.toContain("append.condition-intermediate-event");
    expect(entries).toContain("append.timer-intermediate-event");
    expect(entries).toContain("append.message-intermediate-event");
  });
});

test.describe("GOV — replace menu governance", () => {
  test.use({ actor: "editor" });

  test("GOV-RPL: Task → typed tasks allow; preserve-only deny; MI deny", async ({
    page,
  }) => {
    const modelId = await importModelViaApi(
      "editor",
      "GOV Replace",
      XML_PRESERVE_ONLY,
    );
    await openEditor(page, modelId);
    await selectElement(page, "T1");

    await page
      .locator('.djs-context-pad.open .entry[data-action="replace"]')
      .click();
    const popup = page.locator(".djs-popup");
    await expect(popup).toBeVisible({ timeout: 10_000 });

    const entryIds = await page.evaluate(() =>
      [...document.querySelectorAll(".djs-popup [data-id]")].map((e) =>
        e.getAttribute("data-id"),
      ),
    );

    // CREATE_EDIT continua exposto
    expect(entryIds).toContain("replace-with-user-task");
    expect(entryIds).toContain("replace-with-service-task");
    expect(entryIds).toContain("replace-with-call-activity");

    // preserve-only negado
    expect(entryIds).not.toContain("replace-with-transaction");
    expect(entryIds).not.toContain("replace-with-event-subprocess");
    expect(entryIds).not.toContain("replace-with-collapsed-ad-hoc-subprocess");
    expect(entryIds).not.toContain("replace-with-expanded-ad-hoc-subprocess");

    // MultiInstance/loop headers negados
    expect(entryIds).not.toContain("toggle-parallel-mi");
    expect(entryIds).not.toContain("toggle-sequential-mi");
    expect(entryIds).not.toContain("toggle-loop");
  });

  test("GOV-RPL-GW: gateway → parallel/inclusive/event-based; complex deny", async ({
    page,
  }) => {
    const modelId = await importModelViaApi(
      "editor",
      "GOV Replace GW",
      XML_PRESERVE_ONLY,
    );
    await openEditor(page, modelId);
    await selectElement(page, "EG1");

    await page
      .locator('.djs-context-pad.open .entry[data-action="replace"]')
      .click();
    await expect(page.locator(".djs-popup")).toBeVisible({ timeout: 10_000 });

    const entryIds = await page.evaluate(() =>
      [...document.querySelectorAll(".djs-popup [data-id]")].map((e) =>
        e.getAttribute("data-id"),
      ),
    );
    expect(entryIds).toContain("replace-with-exclusive-gateway");
    expect(entryIds).toContain("replace-with-parallel-gateway");
    expect(entryIds).toContain("replace-with-inclusive-gateway");
    expect(entryIds).not.toContain("replace-with-complex-gateway");
  });
});

test.describe("GOV — properties panel governance", () => {
  test.use({ actor: "editor" });

  test("GOV-PNL: grupos multiInstance/compensation ausentes; isExecutable ausente", async ({
    page,
  }) => {
    const modelId = await importModelViaApi(
      "editor",
      "GOV Panel",
      XML_PRESERVE_ONLY,
    );
    await openEditor(page, modelId);
    await selectElement(page, "T1");

    const panel = page.locator("#bpmn-properties-panel .bio-properties-panel");
    await expect(panel).toBeVisible({ timeout: 10_000 });

    const groupIds = await page.evaluate(() =>
      [
        ...document.querySelectorAll(
          "#bpmn-properties-panel [data-group-id]",
        ),
      ].map((g) => g.getAttribute("data-group-id")),
    );
    expect(groupIds).not.toContain("group-multiInstance");
    expect(groupIds).not.toContain("group-compensation");
    expect(groupIds).not.toContain("group-adHocCompletion");

    // entry isExecutable fora do profile — não renderizado
    await expect(
      page.locator('#bpmn-properties-panel [data-entry-id="isExecutable"]'),
    ).toHaveCount(0);
  });
});

test.describe("GOV — preserve-only integrity", () => {
  test.use({ actor: "editor" });

  test("GOV-PRS: import → edit seguro → autosave → read-back preserva constructs", async ({
    page,
  }) => {
    const modelId = await importModelViaApi(
      "editor",
      "GOV Preserve",
      XML_PRESERVE_ONLY,
    );
    await openEditor(page, modelId);

    // preserve-only renderiza e é selecionável/inspecionável
    for (const id of ["CG1", "TR1", "AH1", "C1", "B1"]) {
      await expect(
        page.locator(`.djs-element[data-element-id="${id}"]`),
      ).toBeVisible();
    }

    // edição segura noutro elemento: rename da task via direct edit
    await selectElement(page, "T1");
    await page
      .locator(`.djs-element[data-element-id="T1"]`)
      .dblclick({ force: true });
    await page.keyboard.type("Editada");
    await page.keyboard.press("Enter");

    // autosave persiste; reload → read-back autoritativo mantém tudo
    await waitSaved(page);
    await page.reload();
    await expect(page.locator(".bpmnm-canvas .djs-container")).toBeVisible({
      timeout: 20_000,
    });
    for (const id of ["CG1", "TR1", "AH1", "C1", "B1"]) {
      await expect(
        page.locator(`.djs-element[data-element-id="${id}"]`),
      ).toBeVisible({ timeout: 15_000 });
    }
  });
});
