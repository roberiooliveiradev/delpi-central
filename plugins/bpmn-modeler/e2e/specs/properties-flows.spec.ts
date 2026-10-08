/**
 * PROP-FLOW (WAVE E) — SequenceFlow BPMN core properties:
 * conditionExpression (set/clear, contexto válido, exclusão com default)
 * e default flow (set, exclusividade, clear, delete sem ref pendurada).
 *
 * Fixture importada via API (di determinístico) — source elegível:
 * Activity (T1) e ExclusiveGateway (G1); inválido: ComplexGateway (G2).
 */
import {
  test,
  expect,
  importModelViaApi,
  waitSaved,
} from "../helpers";
import {
  openEditor,
  selectViaDom,
  focusCanvasSvg,
  saveReadbackReload,
  fetchWorkingCopyXml,
  expectXmlHas,
} from "../ce-helpers";
import {
  expandAllGroups,
  entry,
  entryInput,
  setCheckbox,
  fillEntry,
  clearEntry,
  waitXmlMatch,
} from "../prop-helpers";

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="Defs" targetNamespace="http://bpmn.io/schema/bpmn">' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1"/>' +
  '<bpmn:exclusiveGateway id="G1"/>' +
  '<bpmn:complexGateway id="G2"/>' +
  '<bpmn:task id="T1"/><bpmn:task id="T2"/><bpmn:task id="T3"/>' +
  '<bpmn:task id="T4"/>' +
  '<bpmn:sequenceFlow id="FS" sourceRef="S1" targetRef="G1"/>' +
  '<bpmn:sequenceFlow id="FA" sourceRef="G1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="FB" sourceRef="G1" targetRef="T2"/>' +
  '<bpmn:sequenceFlow id="FC" sourceRef="T1" targetRef="T3"/>' +
  '<bpmn:sequenceFlow id="FD" sourceRef="G2" targetRef="T4"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="80" y="160" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="G1_di" bpmnElement="G1"><dc:Bounds x="220" y="155" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="G2_di" bpmnElement="G2"><dc:Bounds x="220" y="300" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="400" y="60" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T2_di" bpmnElement="T2"><dc:Bounds x="400" y="180" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T3_di" bpmnElement="T3"><dc:Bounds x="620" y="60" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T4_di" bpmnElement="T4"><dc:Bounds x="400" y="290" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="FS_di" bpmnElement="FS"><di:waypoint x="116" y="178"/><di:waypoint x="220" y="178"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="FA_di" bpmnElement="FA"><di:waypoint x="270" y="178"/><di:waypoint x="400" y="100"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="FB_di" bpmnElement="FB"><di:waypoint x="270" y="178"/><di:waypoint x="400" y="220"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="FC_di" bpmnElement="FC"><di:waypoint x="500" y="100"/><di:waypoint x="620" y="100"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="FD_di" bpmnElement="FD"><di:waypoint x="270" y="325"/><di:waypoint x="400" y="330"/></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>";

test.describe("PROP-FLOW — conditionExpression + default flow", () => {
  test.use({ actor: "editor" });

  test("PROP-FLOW-01: conditionExpression set → save → read-back → reload → exclusão com default", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "PROP-FLOW-01", XML);
    await openEditor(page, modelId);

    await selectViaDom(page, "FA");
    await expandAllGroups(page);
    await expect(entry(page, "conditionExpression")).toBeAttached({
      timeout: 10_000,
    });
    await fillEntry(page, "conditionExpression", "amount > 100");

    const xml = await saveReadbackReload(page, "editor", modelId, [
      "FA",
      "FB",
      "FC",
    ]);
    expectXmlHas(
      xml,
      /<bpmn:conditionExpression[^>]*xsi:type="[^"]*FormalExpression"[^>]*>[^<]*amount &gt; 100/,
      "conditionExpression FormalExpression",
    );

    // exclusão mútua: com condition setada, o toggle default sai da UI
    await selectViaDom(page, "FA");
    await expandAllGroups(page);
    await expect(entry(page, "conditionExpression")).toBeAttached();
    await expect(entry(page, "defaultFlow")).toHaveCount(0);
    await expect(entryInput(page, "conditionExpression")).toHaveValue(
      "amount > 100",
    );
  });

  test("PROP-FLOW-02: default flow exclusivity — A default → B default", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "PROP-FLOW-02", XML);
    await openEditor(page, modelId);

    await selectViaDom(page, "FA");
    await expandAllGroups(page);
    await expect(entry(page, "defaultFlow")).toBeAttached({
      timeout: 10_000,
    });
    await setCheckbox(page, "defaultFlow", true);
    let xml = await waitXmlMatch("editor", modelId, /default="FA"/);

    // marca FB → FA deixa de ser default (atributo único no source)
    await selectViaDom(page, "FB");
    await expandAllGroups(page);
    await setCheckbox(page, "defaultFlow", true);
    xml = await waitXmlMatch("editor", modelId, /default="FB"/);
    expect(xml).not.toMatch(/default="FA"/);
    await saveReadbackReload(page, "editor", modelId, ["FA", "FB"]);
  });

  test("PROP-FLOW-03: conditionExpression clear → expression removida (Activity source)", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "PROP-FLOW-03", XML);
    await openEditor(page, modelId);

    // FC sai de uma Activity (T1) — contexto condicional válido
    await selectViaDom(page, "FC");
    await expandAllGroups(page);
    await fillEntry(page, "conditionExpression", "y < 5");
    await waitXmlMatch("editor", modelId, /<bpmn:conditionExpression/);

    await selectViaDom(page, "FC");
    await expandAllGroups(page);
    await clearEntry(page, "conditionExpression");
    const xml = await waitXmlMatch(
      "editor",
      modelId,
      /<bpmn:conditionExpression/,
      false,
    );
    await saveReadbackReload(page, "editor", modelId, ["FC"]);
    // sem condition, o toggle default volta a aparecer
    await selectViaDom(page, "FC");
    await expandAllGroups(page);
    await expect(entry(page, "defaultFlow")).toBeAttached();
  });

  test("PROP-FLOW-04: default flow clear → source.default ausente", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "PROP-FLOW-04", XML);
    await openEditor(page, modelId);

    await selectViaDom(page, "FA");
    await expandAllGroups(page);
    await setCheckbox(page, "defaultFlow", true);
    await waitXmlMatch("editor", modelId, /default="FA"/);

    await selectViaDom(page, "FA");
    await expandAllGroups(page);
    await setCheckbox(page, "defaultFlow", false);
    await waitXmlMatch("editor", modelId, /default="/, false);
    await saveReadbackReload(page, "editor", modelId, ["FA"]);
  });

  test("PROP-FLOW-05: delete do default flow não deixa ref pendurada (vendor UnsetDefaultFlowBehavior)", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "PROP-FLOW-05", XML);
    await openEditor(page, modelId);

    await selectViaDom(page, "FA");
    await expandAllGroups(page);
    await setCheckbox(page, "defaultFlow", true);
    await waitXmlMatch("editor", modelId, /default="FA"/);

    // delete da flow default → source.default não aponta p/ id inexistente
    await selectViaDom(page, "FA");
    await focusCanvasSvg(page);
    await page.keyboard.press("Delete");
    let xml = await waitXmlMatch("editor", modelId, /id="FA"/, false);
    expect(xml).not.toMatch(/default="/);

    // undo restaura a flow E o default atomicamente
    await page.keyboard.press("ControlOrMeta+z");
    xml = await waitXmlMatch("editor", modelId, /id="FA"/);
    expectXmlHas(xml, /default="FA"/, "default restored by undo");
  });

  test("PROP-FLOW-06: contexto inválido — flow de ComplexGateway não expõe grupo flow", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("editor", "PROP-FLOW-06", XML);
    await openEditor(page, modelId);

    await selectViaDom(page, "FD");
    await expandAllGroups(page);
    // ComplexGateway não é fonte válida de condition/default (BPMN core)
    await expect(entry(page, "conditionExpression")).toHaveCount(0);
    await expect(entry(page, "defaultFlow")).toHaveCount(0);
  });
});
