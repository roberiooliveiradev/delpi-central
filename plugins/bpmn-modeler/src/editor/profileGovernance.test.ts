// @vitest-environment jsdom
/**
 * GOV — integration tests da profile governance (G2A).
 *
 * Monta o Modeler real via BpmnEditorAdapter e prova que as surfaces
 * vendor governadas (palette, context pad, replace menu, properties panel)
 * respeitam a editing profile central: preserve-only/out-of-profile não
 * aparecem como create/replace; CREATE_EDIT continua disponível.
 */
import { describe, it, expect, beforeAll, beforeEach, afterEach, vi } from "vitest";
import { BpmnEditorAdapter } from "./BpmnEditorAdapter";
import { installCanvasDomStubs } from "./canvasTestSetup";
import {
  isPaletteEntryAllowed,
  isContextPadEntryAllowed,
  isReplaceEntryAllowed,
  isReplaceHeaderAllowed,
  isPropertiesEntryAllowed,
} from "./editingProfile";

const BPMN_HEADER =
  '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="Definitions_1" targetNamespace="urn:test" ' +
  'exporter="test" exporterVersion="1.0">';

/** Modelo com constructs in-profile E preserve-only importados. */
const DI_XML =
  BPMN_HEADER +
  '  <bpmn:process id="Process_1" isExecutable="true">' +
  '    <bpmn:startEvent id="S1"/>' +
  '    <bpmn:task id="T1"/>' +
  '    <bpmn:exclusiveGateway id="G1"/>' +
  '    <bpmn:eventBasedGateway id="EG1"/>' +
  '    <bpmn:complexGateway id="CG1"/>' +
  '    <bpmn:transaction id="TR1"/>' +
  '    <bpmn:adHocSubProcess id="AH1"/>' +
  '    <bpmn:boundaryEvent id="B1" attachedToRef="T1">' +
  '      <bpmn:messageEventDefinition id="MED1"/>' +
  "    </bpmn:boundaryEvent>" +
  '    <bpmn:boundaryEvent id="B2" attachedToRef="T1">' +
  '      <bpmn:compensateEventDefinition id="CPD1"/>' +
  "    </bpmn:boundaryEvent>" +
  "  </bpmn:process>" +
  '  <bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="Process_1">' +
  '    <bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="0" y="0" width="36" height="36"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="60" y="0" width="100" height="80"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="G1_di" bpmnElement="G1"><dc:Bounds x="200" y="0" width="50" height="50"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="EG1_di" bpmnElement="EG1"><dc:Bounds x="280" y="0" width="50" height="50"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="CG1_di" bpmnElement="CG1"><dc:Bounds x="360" y="0" width="50" height="50"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="TR1_di" bpmnElement="TR1"><dc:Bounds x="0" y="140" width="200" height="150"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="AH1_di" bpmnElement="AH1"><dc:Bounds x="240" y="140" width="200" height="150"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="B1_di" bpmnElement="B1"><dc:Bounds x="80" y="62" width="36" height="36"/></bpmndi:BPMNShape>' +
  '    <bpmndi:BPMNShape id="B2_di" bpmnElement="B2"><dc:Bounds x="250" y="62" width="36" height="36"/></bpmndi:BPMNShape>' +
  "  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>" +
  "</bpmn:definitions>";

/* eslint-disable @typescript-eslint/no-explicit-any */

type AnySvc = Record<string, any>;

function modelerOf(adapter: BpmnEditorAdapter): any {
  return (adapter as unknown as { modeler: any }).modeler;
}

function svc(adapter: BpmnEditorAdapter, name: string): AnySvc {
  const m = modelerOf(adapter);
  if (!m) throw new Error(`no modeler for ${name}`);
  return m.get(name);
}

function element(adapter: BpmnEditorAdapter, id: string): any {
  const registry = svc(adapter, "elementRegistry");
  const el = registry.get(id);
  if (!el) throw new Error(`element ${id} not found`);
  return el;
}

let container: HTMLDivElement;
let panelHost: HTMLDivElement;

beforeAll(() => installCanvasDomStubs());

beforeEach(() => {
  container = document.createElement("div");
  panelHost = document.createElement("div");
  panelHost.id = "bpmn-properties-panel";
  document.body.append(container, panelHost);
});

afterEach(() => {
  document.body.innerHTML = "";
});

describe("GOV — palette governance", () => {
  it("GOV-01: palette só expõe entries classificadas no profile", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const paletteProvider = svc(adapter, "paletteProvider");
    const keys = Object.keys(paletteProvider.getPaletteEntries());
    expect(keys.length).toBeGreaterThan(0);
    for (const key of keys) {
      expect(isPaletteEntryAllowed(key), `unexpected palette entry ${key}`).toBe(true);
    }
    // fail-closed: nenhum create fora do profile
    expect(keys).not.toContain("create.transaction");
    expect(keys).not.toContain("create.complex-gateway");

    adapter.destroy();
  });
});

describe("GOV — replace menu governance", () => {
  it("GOV-02: Task → typed tasks allow; transaction/subprocess-tipos preserve-only deny", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const provider = svc(adapter, "replaceMenuProvider");
    const task = element(adapter, "T1");
    const keys = Object.keys(provider.getPopupMenuEntries(task));

    expect(keys).toContain("replace-with-user-task");
    expect(keys).toContain("replace-with-service-task");
    expect(keys).toContain("replace-with-call-activity");
    expect(keys).not.toContain("replace-with-transaction");
    expect(keys).not.toContain("replace-with-event-subprocess");
    expect(keys).not.toContain("replace-with-collapsed-ad-hoc-subprocess");
    expect(keys).not.toContain("replace-with-expanded-ad-hoc-subprocess");
    for (const key of keys) {
      expect(isReplaceEntryAllowed(key), key).toBe(true);
    }

    adapter.destroy();
  });

  it("GOV-03: Gateway → parallel/inclusive/event-based allow; complex deny", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const provider = svc(adapter, "replaceMenuProvider");
    const gw = element(adapter, "G1");
    const keys = Object.keys(provider.getPopupMenuEntries(gw));

    expect(keys).toContain("replace-with-parallel-gateway");
    expect(keys).toContain("replace-with-inclusive-gateway");
    expect(keys).toContain("replace-with-event-based-gateway");
    expect(keys).not.toContain("replace-with-complex-gateway");

    adapter.destroy();
  });

  it("GOV-04: Start event → message/timer/signal allow; conditional deny", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const provider = svc(adapter, "replaceMenuProvider");
    const start = element(adapter, "S1");
    const keys = Object.keys(provider.getPopupMenuEntries(start));

    expect(keys).toContain("replace-with-message-start");
    expect(keys).toContain("replace-with-timer-start");
    expect(keys).toContain("replace-with-signal-start");
    expect(keys).not.toContain("replace-with-conditional-start");
    expect(keys).not.toContain("replace-with-error-start");
    expect(keys).not.toContain("replace-with-compensation-start");

    adapter.destroy();
  });

  it("GOV-05: Boundary event → defs allow; none/conditional/cancel/compensation deny", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const provider = svc(adapter, "replaceMenuProvider");
    const boundary = element(adapter, "B1");
    const keys = Object.keys(provider.getPopupMenuEntries(boundary));

    // boundary CREATE_EDIT exige definição aprovada — None não é replace target
    expect(keys).not.toContain("replace-with-none-boundary-event");
    expect(keys).not.toContain("replace-with-conditional-boundary");
    expect(keys).not.toContain("replace-with-cancel-boundary");
    expect(keys).not.toContain("replace-with-compensation-boundary");
    expect(keys).not.toContain("replace-with-non-interrupting-conditional-boundary");

    adapter.destroy();
  });

  it("GOV-06: header toggles — MultiInstance/loop/multiplicity negados", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const provider = svc(adapter, "replaceMenuProvider");
    const task = element(adapter, "T1");
    const headers = Object.keys(provider.getPopupMenuHeaderEntries(task));

    expect(headers).not.toContain("toggle-parallel-mi");
    expect(headers).not.toContain("toggle-sequential-mi");
    expect(headers).not.toContain("toggle-loop");
    for (const key of headers) {
      expect(isReplaceHeaderAllowed(key), key).toBe(true);
    }

    adapter.destroy();
  });

  it("GOV-07: preserve-only source (transaction) não oferece replace", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const provider = svc(adapter, "replaceMenuProvider");
    const transaction = element(adapter, "TR1");
    const keys = Object.keys(provider.getPopupMenuEntries(transaction));
    for (const key of keys) {
      expect(isReplaceEntryAllowed(key), key).toBe(true);
    }

    adapter.destroy();
  });
});

describe("GOV — context pad governance", () => {
  it("GOV-08: EventBasedGateway não oferece conditional catch append", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const pad = svc(adapter, "contextPadProvider");
    const ebg = element(adapter, "EG1");
    const keys = Object.keys(pad.getContextPadEntries(ebg));

    expect(keys).not.toContain("append.condition-intermediate-event");
    expect(keys).toContain("append.timer-intermediate-event");
    expect(keys).toContain("append.message-intermediate-event");
    expect(keys).toContain("append.signal-intermediate-event");
    for (const key of keys) {
      expect(isContextPadEntryAllowed(key), key).toBe(true);
    }

    adapter.destroy();
  });

  it("GOV-09: Task context pad — append task/gateway/end-event inalterado", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const pad = svc(adapter, "contextPadProvider");
    const task = element(adapter, "T1");
    const keys = Object.keys(pad.getContextPadEntries(task));

    expect(keys).toContain("append.append-task");
    expect(keys).toContain("append.gateway");
    expect(keys).toContain("append.end-event");
    expect(keys).toContain("replace");
    expect(keys).toContain("connect");
    for (const key of keys) {
      expect(isContextPadEntryAllowed(key), key).toBe(true);
    }

    adapter.destroy();
  });

  it("GOV-11: boundary c/ compensate def não vira bypass de criação (C3)", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);

    const pad = svc(adapter, "contextPadProvider");
    const boundary = element(adapter, "B2");
    const keys = Object.keys(pad.getContextPadEntries(boundary));

    // preserve-only importado não pode virar fonte de criação semântica nova
    expect(keys).not.toContain("append.compensation-activity");
    for (const key of keys) {
      expect(isContextPadEntryAllowed(key), key).toBe(true);
    }

    adapter.destroy();
  });
});

describe("GOV — properties panel governance", () => {
  it("GOV-10: grupos multiInstance/compensation/adHocCompletion ausentes", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);
    adapter.selectElement("T1");

    await vi.waitFor(() => {
      expect(panelHost.querySelector(".bio-properties-panel")).toBeTruthy();
    });

    const groupIds = [
      ...panelHost.querySelectorAll("[data-group-id]"),
    ].map((g) =>
      (g.getAttribute("data-group-id") ?? "").replace(/^group-/, ""),
    );
    expect(groupIds).not.toContain("multiInstance");
    expect(groupIds).not.toContain("compensation");
    expect(groupIds).not.toContain("adHocCompletion");
    expect(groupIds).toContain("general");

    adapter.destroy();
  });

  it("GOV-12: entries do panel são allowlist — aprovados renderizam, isExecutable ausente", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML);
    adapter.selectElement("T1");

    await vi.waitFor(() => {
      expect(panelHost.querySelector(".bio-properties-panel")).toBeTruthy();
    });

    const entryIds = [
      ...panelHost.querySelectorAll("[data-entry-id]"),
    ].map((e) => e.getAttribute("data-entry-id") ?? "");

    // aprovados presentes (name no general; id movido p/ advanced)
    expect(entryIds).toContain("name");
    // isExecutable (normativo, edição intencionalmente oculta) ausente
    expect(entryIds).not.toContain("isExecutable");
    // toda entry renderizada passa na allowlist central (fail-closed)
    for (const id of entryIds) {
      expect(
        isPropertiesEntryAllowed(id),
        `entry não classificada exposta: ${id}`,
      ).toBe(true);
    }

    adapter.destroy();
  });

  it("GOV-13: isExecutable normativo importado é preservado no XML (C4)", async () => {
    const adapter = new BpmnEditorAdapter();
    adapter.mount(container, "edit");
    await adapter.importXml(DI_XML); // DI_XML usa isExecutable="true"

    const xml = await adapter.exportXml();
    expect(xml).toContain('isExecutable="true"');
    // boundary c/ compensate def preserve-only também preservado
    expect(xml).toContain("compensateEventDefinition");

    adapter.destroy();
  });
});
