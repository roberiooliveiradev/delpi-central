// @vitest-environment jsdom
/**
 * CANVAS-REG-01..10 — regression gate do canvas BPMN.
 *
 * Protege o contrato do BpmnEditorAdapter contra drifts de dependência
 * (bpmn-js, properties panel, federation, build). Não testa o DOM interno
 * do vendor — testa o contrato observável do adapter sobre jsdom.
 */
import { describe, it, expect, beforeAll, beforeEach, afterEach, vi } from "vitest";
import { BpmnEditorAdapter } from "./BpmnEditorAdapter";
import { installCanvasDomStubs } from "./canvasTestSetup";

const BPMN_HEADER =
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="Definitions_1" targetNamespace="urn:test" ' +
  'exporter="test" exporterVersion="1.0">';

const BLANK_XML =
  BPMN_HEADER +
  '  <bpmn:process id="Process_1" isExecutable="false"/>' +
  '  <bpmndi:BPMNDiagram id="D1">' +
  '    <bpmndi:BPMNPlane id="P1" bpmnElement="Process_1"/>' +
  "  </bpmndi:BPMNDiagram>" +
  "</bpmn:definitions>";

const DI_XML =
  BPMN_HEADER +
  '  <bpmn:process id="Process_1" isExecutable="false">' +
  '    <bpmn:startEvent id="Start_1"/>' +
  '    <bpmn:task id="Task_1"/>' +
  '    <bpmn:task id="Task_2"/>' +
  '    <bpmn:endEvent id="End_1"/>' +
  '    <bpmn:sequenceFlow id="F1" sourceRef="Start_1" targetRef="Task_1"/>' +
  '    <bpmn:sequenceFlow id="F2" sourceRef="Task_1" targetRef="Task_2"/>' +
  '    <bpmn:sequenceFlow id="F3" sourceRef="Task_2" targetRef="End_1"/>' +
  "  </bpmn:process>" +
  '  <bpmndi:BPMNDiagram id="D1">' +
  '    <bpmndi:BPMNPlane id="P1" bpmnElement="Process_1">' +
  '      <bpmndi:BPMNShape id="S1" bpmnElement="Start_1"><dc:Bounds x="10" y="10" width="36" height="36"/></bpmndi:BPMNShape>' +
  '      <bpmndi:BPMNShape id="S2" bpmnElement="Task_1"><dc:Bounds x="100" y="10" width="100" height="80"/></bpmndi:BPMNShape>' +
  '      <bpmndi:BPMNShape id="S3" bpmnElement="Task_2"><dc:Bounds x="250" y="10" width="100" height="80"/></bpmndi:BPMNShape>' +
  '      <bpmndi:BPMNShape id="S4" bpmnElement="End_1"><dc:Bounds x="400" y="10" width="36" height="36"/></bpmndi:BPMNShape>' +
  '      <bpmndi:BPMNEdge id="E1" bpmnElement="F1"><di:waypoint x="46" y="28"/><di:waypoint x="100" y="50"/></bpmndi:BPMNEdge>' +
  '      <bpmndi:BPMNEdge id="E2" bpmnElement="F2"><di:waypoint x="200" y="50"/><di:waypoint x="250" y="50"/></bpmndi:BPMNEdge>' +
  '      <bpmndi:BPMNEdge id="E3" bpmnElement="F3"><di:waypoint x="350" y="50"/><di:waypoint x="400" y="28"/></bpmndi:BPMNEdge>' +
  "    </bpmndi:BPMNPlane>" +
  "  </bpmndi:BPMNDiagram>" +
  "</bpmn:definitions>";

/** Acesso introspectivo somente para assert de identidade de instância (REG-09). */
function instanceOf(adapter: BpmnEditorAdapter): unknown {
  return (adapter as unknown as { modeler: unknown }).modeler;
}

function service<T>(adapter: BpmnEditorAdapter, name: string): T {
  const modeler = instanceOf(adapter) as { get(n: string): T } | null;
  if (!modeler) throw new Error(`no modeler for service ${name}`);
  return modeler.get(name);
}

let container: HTMLDivElement;
let panelHost: HTMLDivElement;

beforeAll(() => {
  installCanvasDomStubs();
});

beforeEach(() => {
  container = document.createElement("div");
  panelHost = document.createElement("div");
  panelHost.id = "bpmn-properties-panel";
  document.body.append(container, panelHost);
});

afterEach(() => {
  document.body.innerHTML = "";
});

describe("CANVAS-REG — regression gate do canvas BPMN", () => {
  it("CANVAS-REG-01 mount editor once — monta uma instância e não duplica container", () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    expect(instanceOf(adapter)).toBeTruthy();
    expect(container.querySelectorAll(".bjs-container").length).toBe(1);
    adapter.destroy();
  });

  it("CANVAS-REG-02 import blank BPMN — modelo vazio abre sem erro", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    const result = await adapter.importXml(BLANK_XML);
    expect(result.ok).toBe(true);
    adapter.destroy();
  });

  it("CANVAS-REG-03 import representative BPMN with DI — elementos registrados", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    const result = await adapter.importXml(DI_XML);
    expect(result.ok).toBe(true);
    expect(adapter.findElements({ id: "Task_1" })).toHaveLength(1);
    expect(adapter.findElements({ id: "Task_2" })).toHaveLength(1);
    adapter.destroy();
  });

  it("CANVAS-REG-04 pan/zoom/fit — zoomIn/zoomOut/fitViewport alteram escala", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);
    const canvas = service<{ viewbox(): { scale: number } }>(adapter, "canvas");
    const initial = canvas.viewbox().scale;
    adapter.zoomIn();
    const zoomed = canvas.viewbox().scale;
    expect(zoomed).toBeGreaterThan(initial);
    adapter.zoomOut();
    adapter.fitViewport();
    expect(canvas.viewbox().scale).toBeGreaterThan(0);
    adapter.destroy();
  });

  it("CANVAS-REG-05 select element — selection.changed emite ids", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);
    const selected: string[][] = [];
    adapter.subscribe({ onSelectionChanged: (ids) => selected.push(ids) });
    adapter.selectElement("Task_1");
    expect(selected.at(-1)).toEqual(["Task_1"]);
    adapter.destroy();
  });

  it("CANVAS-REG-06 properties panel receives selection — painel renderiza entries", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);
    adapter.selectElement("Task_1");
    await vi.waitFor(() => {
      expect(
        panelHost.querySelector(".bio-properties-panel"),
      ).toBeTruthy();
    });
    adapter.destroy();
  });

  it("CANVAS-REG-07 unmount/destroy cleanly — remove DOM e tolera chamadas", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);
    adapter.destroy();
    expect(instanceOf(adapter)).toBeNull();
    expect(container.querySelectorAll(".bjs-container").length).toBe(0);
    expect(() => adapter.destroy()).not.toThrow();
    adapter.undo();
    adapter.zoomIn();
    adapter.selectElement("Task_1");
  });

  it("CANVAS-REG-08 read-only viewer renders — sem commandStack/dirty", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "viewer");
    const result = await adapter.importXml(DI_XML);
    expect(result.ok).toBe(true);
    expect(container.querySelectorAll(".bjs-container").length).toBe(1);
    expect(adapter.canUndo()).toBe(false);
    expect(adapter.canRedo()).toBe(false);
    expect(adapter.isDirty()).toBe(false);
    adapter.destroy();
  });

  it("CANVAS-REG-09 editor instance not recreated on unrelated operations", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    const first = instanceOf(adapter);
    await adapter.importXml(DI_XML);
    adapter.isDirty();
    adapter.markSaved();
    adapter.findElements({ id: "Task_1" });
    adapter.subscribe({});
    expect(instanceOf(adapter)).toBe(first);
    adapter.mount(container, "edit");
    const second = instanceOf(adapter);
    expect(second).not.toBe(first);
    adapter.destroy();
  });

  it("CANVAS-REG-10 exportXml after load remains valid BPMN", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);
    const xml = await adapter.exportXml();
    expect(xml).toContain("bpmn:definitions");
    expect(xml).toContain('id="Task_1"');
    expect(xml).toContain("bpmndi:BPMNShape");
    const reimport = await adapter.importXml(xml);
    expect(reimport.ok).toBe(true);
    adapter.destroy();
  });
});
