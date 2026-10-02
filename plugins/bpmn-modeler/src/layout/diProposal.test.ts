// @vitest-environment jsdom
/**
 * snapshotFromXml — containers não-nó (process/collaboration/laneSet)
 * repassam parentId; nós internos a um processo simples não podem
 * ficar órfãos (regressão: grafo ELK vazio → canvas em branco).
 */
import { describe, expect, it } from "vitest";

import { buildElkGraph } from "./elkGraph";
import {
  buildDiOps,
  buildDiXml,
  hasBpmnDi,
  planeElementFor,
  snapshotFromXml,
} from "./diProposal";

const HEAD =
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs" targetNamespace="urn:t">';

const SIMPLE =
  HEAD +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:startEvent id="S1"/><bpmn:task id="T1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  "</bpmn:process></bpmn:definitions>";

const NESTED =
  HEAD +
  '<bpmn:process id="P1">' +
  '<bpmn:subProcess id="SUB1"><bpmn:task id="INNER"/></bpmn:subProcess>' +
  '<bpmn:task id="T1"/>' +
  "</bpmn:process></bpmn:definitions>";

const LANES =
  HEAD +
  '<bpmn:process id="P1"><bpmn:laneSet id="LS1">' +
  '<bpmn:lane id="L1"><bpmn:flowNodeRef>T1</bpmn:flowNodeRef></bpmn:lane>' +
  "</bpmn:laneSet><bpmn:task id=\"T1\"/></bpmn:process></bpmn:definitions>";

describe("snapshotFromXml", () => {
  it("promove filhos de <process> para a raiz (sem órfãos)", () => {
    const s = snapshotFromXml(SIMPLE);
    expect(s.nodes.map((n) => n.id).sort()).toEqual(["S1", "T1"]);
    expect(s.nodes.every((n) => n.parentId === undefined)).toBe(true);
    expect(s.edges).toEqual([
      { id: "F1", sourceId: "S1", targetId: "T1" },
    ]);
    const graph = buildElkGraph(s);
    expect(graph.children?.map((c) => c.id).sort()).toEqual(["S1", "T1"]);
    expect(graph.edges?.map((e) => e.id)).toEqual(["F1"]);
  });

  it("subProcess é nó e seus filhos ficam aninhados", () => {
    const s = snapshotFromXml(NESTED);
    const sub = s.nodes.find((n) => n.id === "SUB1");
    const inner = s.nodes.find((n) => n.id === "INNER");
    expect(sub?.parentId).toBeUndefined();
    expect(inner?.parentId).toBe("SUB1");
    const graph = buildElkGraph(s);
    const subNode = graph.children?.find((c) => c.id === "SUB1");
    expect(subNode?.children?.[0]?.id).toBe("INNER");
  });

  it("lane.flowNodeRef dirige o containment: membro vira child da lane", () => {
    const s = snapshotFromXml(LANES);
    expect(s.nodes.find((n) => n.id === "L1")?.parentId).toBeUndefined();
    expect(s.nodes.find((n) => n.id === "T1")?.parentId).toBe("L1");
  });

  it("captura bounds DI vigentes no snapshot (fonte do tamanho)", () => {
    const xml =
      SIMPLE.replace("</bpmn:definitions>",
        '<bpmndi:BPMNDiagram id="d1"><bpmndi:BPMNPlane id="p1" bpmnElement="P1">' +
        '<bpmndi:BPMNShape id="s_T1" bpmnElement="T1">' +
        '<dc:Bounds x="50" y="60" width="140" height="90"/></bpmndi:BPMNShape>' +
        '<bpmndi:BPMNShape id="s_S1" bpmnElement="S1">' +
        '<dc:Bounds x="10" y="10" width="36" height="36"/></bpmndi:BPMNShape>' +
        "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>");
    const s = snapshotFromXml(xml);
    expect(s.nodes.find((n) => n.id === "T1")).toMatchObject({
      width: 140,
      height: 90,
    });
    expect(s.nodes.find((n) => n.id === "S1")).toMatchObject({
      width: 36,
      height: 36,
    });
  });

  it("hasBpmnDi/planeElementFor respeitam o artefato", () => {
    expect(hasBpmnDi(SIMPLE)).toBe(false);
    expect(planeElementFor(SIMPLE)).toBe("P1");
    expect(hasBpmnDi(SIMPLE.replace("</bpmn:definitions>",
      '<bpmndi:BPMNDiagram id="d1"/></bpmn:definitions>'))).toBe(true);
  });
});

describe("size preservation policy", () => {
  it("ELK input usa bounds atuais; default vendor só sem DI", () => {
    const s = snapshotFromXml(SIMPLE);
    const g = buildElkGraph(s);
    const t1 = g.children?.find((c) => c.id === "T1");
    expect(t1?.width).toBe(100); // fallback do profile sem DI

    const sized = {
      nodes: s.nodes.map((n) =>
        n.id === "T1" ? { ...n, width: 160, height: 120 } : n,
      ),
      edges: s.edges,
    };
    const g2 = buildElkGraph(sized);
    expect(g2.children?.find((c) => c.id === "T1")?.width).toBe(160);
    expect(g2.children?.find((c) => c.id === "T1")?.height).toBe(120);
  });

  it("buildDiOps preserva w/h de não-container mesmo se ELK mudou", () => {
    const snapshot = {
      nodes: [
        { id: "T1", type: "bpmn:task", width: 160, height: 120 },
        { id: "S1", type: "bpmn:startEvent", width: 36, height: 36 },
        { id: "SUB1", type: "bpmn:subProcess", width: 350, height: 200 },
        { id: "POOL", type: "bpmn:participant", isParticipant: true, width: 700, height: 300 },
      ],
      edges: [],
    };
    const laidOut = {
      id: "__root__",
      children: [
        { id: "T1", x: 300, y: 200, width: 100, height: 80 }, // ELK "encolheu"
        { id: "S1", x: 0, y: 0, width: 50, height: 50 },
        { id: "SUB1", x: 0, y: 300, width: 400, height: 260 }, // container pode
        { id: "POOL", x: 0, y: 600, width: 800, height: 400 },
      ],
    };
    const ops = buildDiOps(laidOut, snapshot);
    const byId = new Map(ops.map((o) => [o.elementId, o.bounds]));

    // SIZE_PRESERVED: x/y novos do ELK, w/h vigentes
    expect(byId.get("T1")).toMatchObject({ x: 300, y: 200, width: 160, height: 120 });
    expect(byId.get("S1")).toMatchObject({ x: 0, y: 0, width: 36, height: 36 });
    // LAYOUT_MAY_RESIZE: containers aceitam o tamanho do ELK
    expect(byId.get("SUB1")).toMatchObject({ width: 400, height: 260 });
    expect(byId.get("POOL")).toMatchObject({ width: 800, height: 400 });
  });

  it("label externa acompanha o owner pelo delta; edge pelo mid", () => {
    // shape T1 move de (10,10)→(300,300); label (15,100,60,14) → +290/+290
    // edge F1 mid (0,0)→(100,100) → label (5,5,40,14) → +95/+95... verificar mid
    const snapshot = {
      nodes: [
        { id: "T1", type: "bpmn:task", x: 10, y: 10, width: 100, height: 80,
          labelBounds: { x: 15, y: 100, width: 60, height: 14 } },
      ],
      edges: [
        { id: "F1", sourceId: "T1", targetId: "T2",
          points: [{ x: 0, y: 0 }, { x: 100, y: 0 }],
          labelBounds: { x: 40, y: -20, width: 40, height: 14 } },
      ],
    };
    const laidOut = {
      id: "__root__",
      children: [{ id: "T1", x: 300, y: 300, width: 100, height: 80 }],
      edges: [
        { id: "F1", sources: ["T1"], targets: ["T2"],
          sections: [{ startPoint: { x: 300, y: 200 }, endPoint: { x: 500, y: 200 } }] },
      ],
    };
    const ops = buildDiOps(laidOut, snapshot);
    const t1 = ops.find((o) => o.elementId === "T1")!;
    expect(t1.labelBounds).toMatchObject({
      x: 305,
      y: 390,
      width: 60,
      height: 14,
    });
    const f1 = ops.find((o) => o.elementId === "F1")!;
    // edge old mid = (50,0); new mid = (400,200) → label +350/+200
    expect(f1.labelBounds).toMatchObject({
      x: 390,
      y: 180,
      width: 40,
      height: 14,
    });
  });

  it("nó sem BPMNLabel no DI não emite labelBounds (vendor auto-posiciona)", () => {
    const snapshot = {
      nodes: [{ id: "T1", type: "bpmn:task", x: 0, y: 0, width: 100, height: 80 }],
      edges: [],
    };
    const laidOut = {
      id: "__root__",
      children: [{ id: "T1", x: 50, y: 50, width: 100, height: 80 }],
    };
    expect(buildDiOps(laidOut, snapshot)[0].labelBounds).toBeUndefined();
  });

  it("nó sem DI vigente aceita o tamanho ELK (primeiro layout)", () => {
    const snapshot = { nodes: [{ id: "T1", type: "bpmn:task" }], edges: [] };
    const laidOut = {
      id: "__root__",
      children: [{ id: "T1", x: 10, y: 20, width: 100, height: 80 }],
    };
    const ops = buildDiOps(laidOut, snapshot);
    expect(ops[0].bounds).toMatchObject({ width: 100, height: 80 });
  });
});

describe("hierarquia semântica → ELK", () => {
  /** Pool + 2 lanes + subProcess expandido + collapsed + dataObject. */
  const POOL =
    HEAD +
    '<bpmn:collaboration id="C1">' +
    '<bpmn:participant id="POOL1" processRef="P1"/>' +
    '<bpmn:participant id="POOL2" processRef="P2"/>' +
    '<bpmn:messageFlow id="MF1" sourceRef="T_B" targetRef="T1"/>' +
    "</bpmn:collaboration>" +
    '<bpmn:process id="P1"><bpmn:laneSet>' +
    '<bpmn:lane id="LANE_A">' +
    "<bpmn:flowNodeRef>S1</bpmn:flowNodeRef><bpmn:flowNodeRef>T1</bpmn:flowNodeRef>" +
    "<bpmn:flowNodeRef>SUB1</bpmn:flowNodeRef><bpmn:flowNodeRef>SUBC</bpmn:flowNodeRef></bpmn:lane>" +
    '<bpmn:lane id="LANE_B"><bpmn:flowNodeRef>T2</bpmn:flowNodeRef>' +
    "<bpmn:flowNodeRef>E1</bpmn:flowNodeRef></bpmn:lane>" +
    "</bpmn:laneSet>" +
    '<bpmn:startEvent id="S1"/><bpmn:task id="T1"/>' +
    '<bpmn:task id="T2"/><bpmn:endEvent id="E1"/>' +
    '<bpmn:dataStoreReference id="DS1"/>' +
    '<bpmn:subProcess id="SUB1"><bpmn:task id="ST1"/></bpmn:subProcess>' +
    '<bpmn:subProcess id="SUBC"><bpmn:task id="SC1"/></bpmn:subProcess>' +
    '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
    '<bpmn:sequenceFlow id="FX" sourceRef="T1" targetRef="T2"/>' +
    "</bpmn:process>" +
    '<bpmn:process id="P2"><bpmn:task id="T_B"/></bpmn:process>' +
    '<bpmndi:BPMNDiagram id="D"><bpmndi:BPMNPlane id="PL" bpmnElement="C1">' +
    '<bpmndi:BPMNShape id="sp_POOL1" bpmnElement="POOL1" isHorizontal="true">' +
    '<dc:Bounds x="0" y="0" width="800" height="400"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_POOL2" bpmnElement="POOL2" isHorizontal="true">' +
    '<dc:Bounds x="0" y="500" width="800" height="200"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_LANE_A" bpmnElement="LANE_A">' +
    '<dc:Bounds x="30" y="0" width="770" height="200"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_LANE_B" bpmnElement="LANE_B">' +
    '<dc:Bounds x="30" y="200" width="770" height="200"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_S1" bpmnElement="S1"><dc:Bounds x="50" y="50" width="36" height="36"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_T1" bpmnElement="T1"><dc:Bounds x="120" y="30" width="100" height="80"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_T2" bpmnElement="T2"><dc:Bounds x="120" y="230" width="100" height="80"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_E1" bpmnElement="E1"><dc:Bounds x="400" y="250" width="36" height="36"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_DS1" bpmnElement="DS1"><dc:Bounds x="300" y="20" width="50" height="50"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_TB" bpmnElement="T_B"><dc:Bounds x="100" y="560" width="100" height="80"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_SUB1" bpmnElement="SUB1" isExpanded="true">' +
    '<dc:Bounds x="250" y="20" width="350" height="160"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_ST1" bpmnElement="ST1"><dc:Bounds x="270" y="60" width="100" height="80"/></bpmndi:BPMNShape>' +
    '<bpmndi:BPMNShape id="sp_SUBC" bpmnElement="SUBC" isExpanded="false">' +
    '<dc:Bounds x="550" y="30" width="100" height="80"/></bpmndi:BPMNShape>' +
    "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>";

  it("lane members viram children da lane; lanes do participant", () => {
    const s = snapshotFromXml(POOL);
    const parent = (id: string) => s.nodes.find((n) => n.id === id)?.parentId;
    expect(parent("LANE_A")).toBe("POOL1");
    expect(parent("LANE_B")).toBe("POOL1");
    expect(parent("S1")).toBe("LANE_A");
    expect(parent("T1")).toBe("LANE_A");
    expect(parent("SUB1")).toBe("LANE_A");
    expect(parent("SUBC")).toBe("LANE_A"); // collapsed: membro de lane
    expect(parent("ST1")).toBe("SUB1"); // filho do subprocess, não da lane
    expect(parent("T2")).toBe("LANE_B");
    expect(parent("E1")).toBe("LANE_B");
    // DS1 não está em nenhuma lane → região do pool (UNLANED)
    expect(parent("DS1")).toBe("POOL1");
    // T_B pertence a P2 → POOL2
    expect(parent("T_B")).toBe("POOL2");
    expect(parent("POOL1")).toBeUndefined();
    expect(parent("POOL2")).toBeUndefined();
  });

  it("ELK graph espelha a hierarquia; edge cross-lane no LCA (participant)", () => {
    const g = buildElkGraph(snapshotFromXml(POOL));
    const pool1 = g.children?.find((c) => c.id === "POOL1");
    const pool2 = g.children?.find((c) => c.id === "POOL2");
    expect(pool1?.children?.map((c) => c.id).sort()).toEqual([
      "DS1",
      "LANE_A",
      "LANE_B",
    ]);
    const laneA = pool1?.children?.find((c) => c.id === "LANE_A");
    expect(laneA?.children?.map((c) => c.id).sort()).toEqual([
      "S1",
      "SUB1",
      "SUBC",
      "T1",
    ]);
    const sub1 = laneA?.children?.find((c) => c.id === "SUB1");
    expect(sub1?.children?.[0]?.id).toBe("ST1");
    expect(pool2?.children?.[0]?.id).toBe("T_B");
    // F1 (S1→T1) escopo LANE_A; FX (cross-lane) escopo POOL1; MF1 root.
    expect(laneA?.edges?.map((e) => e.id)).toEqual(["F1"]);
    expect(pool1?.edges?.map((e) => e.id)).toEqual(["FX"]);
    expect(g.edges?.map((e) => e.id)).toEqual(["MF1"]);
  });

  it("subProcess collapsed: filhos fora do grafo; size preservado", () => {
    const s = snapshotFromXml(POOL);
    const g = buildElkGraph(s);
    const subc = JSON.stringify(g);
    expect(subc).not.toContain('"SC1"'); // filho de collapsed oculto
    expect(subc).toContain('"SUBC"');
    const ops = buildDiOps(
      {
        id: "__root__",
        children: [
          {
            id: "POOL1",
            x: 0,
            y: 0,
            width: 900,
            height: 500,
            children: [
              {
                id: "LANE_A",
                x: 40,
                y: 10,
                width: 840,
                height: 240,
                children: [
                  { id: "SUBC", x: 500, y: 40, width: 130, height: 110 },
                ],
              },
            ],
          },
        ],
      },
      s,
    );
    // collapsed = SIZE_PRESERVED mesmo se ELK devolveu outro tamanho
    const op = ops.find((o) => o.elementId === "SUBC");
    expect(op?.bounds).toMatchObject({ width: 100, height: 80 });
    expect(ops.find((o) => o.elementId === "SC1")).toBeUndefined();
  });

  it("preview DI preserva atributos do shape original (isExpanded/isHorizontal/id)", () => {
    const s = snapshotFromXml(POOL);
    const g = buildElkGraph(s);
    const xml = buildDiXml(g, s, "C1");
    expect(xml).toContain('id="sp_SUB1"');
    expect(xml).toContain('bpmnElement="SUB1" isExpanded="true"');
    expect(xml).toContain('bpmnElement="SUBC" isExpanded="false"');
    expect(xml).toContain('bpmnElement="POOL1" isHorizontal="true"');
    // filho de collapsed não ganha shape no preview
    expect(xml).not.toContain('bpmnElement="SC1"');
  });
});
