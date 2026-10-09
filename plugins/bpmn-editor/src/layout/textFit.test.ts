// @vitest-environment jsdom
/**
 * text-fit G9 — sizing determinístico por rótulo + integração no snapshot.
 */
import { describe, expect, it } from "vitest";

import {
  applyTextFitSizing,
  snapshotFromXml,
} from "./diProposal";
import { LAYOUT_PROFILE_V1 } from "./layoutProfile";
import {
  estimateTextWidth,
  fitTextSize,
  isTextFitNodeType,
  wrapText,
} from "./textFit";

const HEAD =
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs" targetNamespace="urn:t">';

const LONG_LABEL =
  "Dados são tratados e indicadores calculados automaticamente";

const DOC =
  HEAD +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1" name="Início"/>' +
  `<bpmn:task id="T1" name="${LONG_LABEL}"/>` +
  '<bpmn:task id="T2" name="Ok"/>' +
  '<bpmn:exclusiveGateway id="G1" name="Decisão longa externa"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
  '<bpmndi:BPMNShape id="sT1" bpmnElement="T1"><dc:Bounds x="0" y="0" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sT2" bpmnElement="T2"><dc:Bounds x="0" y="0" width="220" height="120"/></bpmndi:BPMNShape>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>" +
  "</bpmn:definitions>";

describe("estimateTextWidth", () => {
  it("largura cresce com o texto e respeita classes de caractere", () => {
    expect(estimateTextWidth("WWWW", 12)).toBeGreaterThan(
      estimateTextWidth("iiii", 12),
    );
    expect(estimateTextWidth("abcdef", 12)).toBeGreaterThan(0);
  });
});

describe("wrapText", () => {
  it("quebra por palavra, nunca dentro de palavra curta", () => {
    const r = wrapText("aa bb cc", 40, 12);
    expect(r.lines).toBeGreaterThan(1);
    expect(r.lines).toBeLessThanOrEqual(8);
  });

  it("largura grande → uma linha", () => {
    expect(wrapText("aa bb", 10_000, 12).lines).toBe(1);
  });
});

describe("fitTextSize", () => {
  const cfg = LAYOUT_PROFILE_V1.textFit;

  it("texto curto → mínimos", () => {
    const s = fitTextSize("Ok");
    expect(s.width).toBe(cfg.minWidth);
    expect(s.height).toBe(cfg.minHeight);
  });

  it("texto longo → cresce largura primeiro, altura ≥ min", () => {
    const s = fitTextSize(LONG_LABEL);
    expect(s.width).toBeGreaterThan(cfg.minWidth);
    expect(s.width).toBeLessThanOrEqual(cfg.maxWidth);
    expect(s.height).toBeGreaterThanOrEqual(cfg.minHeight);
    expect(s.lines).toBeLessThanOrEqual(cfg.maxLines);
  });

  it("texto gigante → cap maxWidth e altura acompanha linhas", () => {
    const s = fitTextSize(
      "Uma atividade extremamente longa que descreve em detalhe absoluto " +
        "cada etapa do processo corporativo de governança incluindo aprovações " +
        "múltiplas revisões formais e sinalizações de indicadores operacionais",
    );
    expect(s.width).toBeLessThanOrEqual(cfg.maxWidth);
    expect(s.height).toBeLessThanOrEqual(cfg.maxHeight);
    expect(s.lines).toBeGreaterThan(cfg.maxLines);
  });
});

describe("isTextFitNodeType", () => {
  it("task/sim → true; event/gateway/lane → false", () => {
    expect(isTextFitNodeType("bpmn:task")).toBe(true);
    expect(isTextFitNodeType("bpmn:serviceTask")).toBe(true);
    expect(isTextFitNodeType("bpmn:startEvent")).toBe(false);
    expect(isTextFitNodeType("bpmn:exclusiveGateway")).toBe(false);
    expect(isTextFitNodeType("bpmn:lane")).toBe(false);
  });
});

describe("applyTextFitSizing", () => {
  it("task pequena com label longa cresce; shapes com label externa intactas", () => {
    const snap = applyTextFitSizing(snapshotFromXml(DOC));
    const t1 = snap.nodes.find((n) => n.id === "T1")!;
    const g1 = snap.nodes.find((n) => n.id === "G1")!;
    const s1 = snap.nodes.find((n) => n.id === "S1")!;
    expect(t1.width!).toBeGreaterThan(100);
    // gateway/evento mantêm bounds originais/ausentes (label externa)
    expect(g1.width).toBeUndefined();
    expect(s1.width).toBeUndefined();
  });

  it("grow-only: DI maior que o fit é preservado", () => {
    const snap = applyTextFitSizing(snapshotFromXml(DOC));
    const t2 = snap.nodes.find((n) => n.id === "T2")!;
    expect(t2.width).toBe(220);
    expect(t2.height).toBe(120);
  });

  it("subProcess expandido não é redimensionado pela label", () => {
    const doc =
      HEAD +
      '<bpmn:process id="P1">' +
      '<bpmn:subProcess id="SP1" name="Sub processo com nome bem longo mesmo">' +
      '<bpmn:task id="IN"/></bpmn:subProcess>' +
      "</bpmn:process>" +
      '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="P1">' +
      '<bpmndi:BPMNShape id="sSP" bpmnElement="SP1" isExpanded="true"><dc:Bounds x="0" y="0" width="350" height="200"/></bpmndi:BPMNShape>' +
      "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>" +
      "</bpmn:definitions>";
    const snap = applyTextFitSizing(snapshotFromXml(doc));
    expect(snap.nodes.find((n) => n.id === "SP1")!.width).toBe(350);
  });

  it("determinístico: mesmo input → mesmos bounds", () => {
    const a = applyTextFitSizing(snapshotFromXml(DOC));
    const b = applyTextFitSizing(snapshotFromXml(DOC));
    const dims = (s: typeof a) =>
      s.nodes.map((n) => `${n.id}:${n.width}x${n.height}`).join("|");
    expect(dims(a)).toBe(dims(b));
  });
});
