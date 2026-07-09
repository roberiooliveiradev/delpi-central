import { describe, expect, it } from "vitest";

import { emptyFlowchart } from "../types/diagram";
import { autoLayoutFlowchart, withNormalizedLanes } from "./diagramSwimlanes";
import { bpmnMermaidClassForType, buildBpmnCatalogForApi, formatMermaidNodeLine } from "./bpmnMermaidMapping";
import {
  flowchartToMermaid,
  mermaidToFlowchart,
  MermaidImportError,
} from "./flowchartMermaid";

describe("flowchartToMermaid", () => {
  it("gera placeholder para diagrama vazio", () => {
    const text = flowchartToMermaid(emptyFlowchart());
    expect(text).toContain("flowchart TD");
    expect(text.toLowerCase()).toContain("vazio");
  });

  it("renderiza nó de decisão com chaves e classe BPMN", () => {
    const text = flowchartToMermaid({
      format: "flowchart_v1",
      format_version: 1,
      nodes: [
        {
          id: "n_dec",
          type: "decision",
          label: "Aprovado?",
          position: { x: 0, y: 0 },
        },
      ],
      edges: [],
    });
    expect(text).toContain('n_dec{"Aprovado?"}:::bpmn_decision');
    expect(text).toContain("classDef bpmn_gateway_exclusive");
  });

  it("exporta swimlanes como subgraph e tipos distintos", () => {
    const text = flowchartToMermaid({
      format: "flowchart_v1",
      format_version: 1,
      lanes: [{ id: "lane_a", label: "Comercial", height: 168, order: 0 }],
      nodes: [
        {
          id: "n_start",
          type: "start_message",
          label: "Pedido",
          position: { x: 0, y: 0 },
          lane_id: "lane_a",
        },
        {
          id: "n_store",
          type: "data",
          label: "CRM",
          position: { x: 0, y: 0 },
          lane_id: "lane_a",
        },
      ],
      edges: [],
    });
    expect(text).toContain('subgraph lane_lane_a ["Comercial"]');
    expect(text).toContain(":::bpmn_start_message");
    expect(text).toContain('[("CRM")]:::bpmn_data');
    expect(text).toContain("classDef bpmn_event_start");
    expect(text).toContain("classDef bpmn_artifact_data_store");
  });

  it("quebra rótulo longo de faixa em subgraph", () => {
    const text = flowchartToMermaid({
      format: "flowchart_v1",
      format_version: 1,
      lanes: [
        {
          id: "lane_lmp",
          label: "LMP — Lançamento e Modificação de Produtos / Engenharia",
          height: 168,
          order: 0,
        },
      ],
      nodes: [
        {
          id: "n1",
          type: "process",
          label: "Validar",
          position: { x: 200, y: 80 },
          lane_id: "lane_lmp",
        },
      ],
      edges: [],
    });

    expect(text).toContain("subgraph lane_lane_lmp");
    expect(text).toMatch(/LMP — Lançamento e Modificação de<br>Produtos/);
  });

  it("exporta arestas de mensagem e associação", () => {
    const text = flowchartToMermaid({
      format: "flowchart_v1",
      format_version: 1,
      nodes: [
        { id: "a", type: "process", label: "A", position: { x: 0, y: 0 } },
        { id: "b", type: "process", label: "B", position: { x: 0, y: 0 } },
      ],
      edges: [
        { id: "e1", from: "a", to: "b", label: "msg", kind: "message_flow" },
      ],
    });
    expect(text).toContain('a -.->|"msg"| b');
  });
});

describe("mermaidToFlowchart", () => {
  it("importa fluxo linear simples", () => {
    const code = [
      "flowchart TD",
      '    start(("Início")):::bpmn_start',
      '    proc["Atividade"]:::bpmn_process',
      '    end(("Fim")):::bpmn_end',
      "    start --> proc",
      "    proc --> end",
    ].join("\n");

    const chart = mermaidToFlowchart(code);
    expect(chart.nodes).toHaveLength(3);
    expect(chart.nodes[0]?.type).toBe("start");
    expect(chart.nodes[2]?.type).toBe("end");
    expect(chart.edges).toHaveLength(2);
  });

  it("restaura tipo BPMN pela classe mermaid", () => {
    const code = [
      "flowchart TD",
      '    timer(("SLA")):::bpmn_start_timer',
      '    gw{"OK?"}:::bpmn_decision',
    ].join("\n");
    const chart = mermaidToFlowchart(code);
    expect(chart.nodes.find((node) => node.id === "timer")?.type).toBe("start_timer");
    expect(chart.nodes.find((node) => node.id === "gw")?.type).toBe("decision");
  });

  it("importa swimlanes de subgraph", () => {
    const code = [
      "flowchart TD",
      '    subgraph lane_vendas ["Vendas"]',
      '        n1["CRM"]:::bpmn_process',
      "    end",
    ].join("\n");
    const chart = mermaidToFlowchart(code);
    expect(chart.lanes?.[0]?.label).toBe("Vendas");
    expect(chart.nodes[0]?.lane_id).toBe("vendas");
  });

  it("rejeita cabeçalho inválido", () => {
    expect(() => mermaidToFlowchart("graph LR\n    a --> b")).toThrow(MermaidImportError);
  });

  it("round-trip preserva tipos e rótulos principais", () => {
    const original = {
      format: "flowchart_v1" as const,
      format_version: 1 as const,
      nodes: [
        { id: "n1", type: "start" as const, label: "Início", position: { x: 0, y: 0 } },
        { id: "n2", type: "task_user" as const, label: "Passo", position: { x: 0, y: 0 } },
        { id: "n3", type: "end" as const, label: "Fim", position: { x: 0, y: 0 } },
      ],
      edges: [
        { id: "e1", from: "n1", to: "n2", label: null },
        { id: "e2", from: "n2", to: "n3", label: null },
      ],
    };

    const code = flowchartToMermaid(original);
    const imported = mermaidToFlowchart(code);
    expect(imported.nodes.map((node) => node.type)).toEqual(["start", "task_user", "end"]);
    expect(imported.nodes.map((node) => node.label)).toEqual(["Início", "Passo", "Fim"]);
    expect(imported.edges).toHaveLength(2);
  });

  it("importa modelo BPMN com faixas e loops e alinha com auto-layout", () => {
    const code = [
      "flowchart TD",
      '    subgraph lane_lane_e6jo48b ["Comercial"]',
      '        start_pmeju9i(("Recebimento de nova demanda no CRM")):::bpmn_start',
      '        proc_bbifixy["Registrar oportunidade e anexos no CRM"]:::bpmn_process',
      '        proc_aj62bcn["Encaminhar demanda para Engenharia"]:::bpmn_process',
      '        proc_apf5m3k["Solicitar informações faltantes ao cliente"]:::bpmn_process',
      "    end",
      '    subgraph lane_lane_x1grz3h ["LMP — Lançamento e Modificação de Produtos / Engenharia"]',
      '        proc_41s5v2a["Validar informações técnicas recebidas"]:::bpmn_process',
      '        dec_6wp6qxi{"Informações completas?"}:::bpmn_decision',
      '        proc_d9hbj0a["Elaborar lançamento / modificação de produto"]:::bpmn_process',
      '        dec_cxqw47f{"Revisão técnica aprovada?"}:::bpmn_decision',
      '        end_37zuxy5(("Fim")):::bpmn_end',
      "    end",
      "    start_pmeju9i --> proc_bbifixy",
      "    proc_bbifixy --> proc_aj62bcn",
      "    proc_aj62bcn --> proc_41s5v2a",
      "    proc_41s5v2a --> dec_6wp6qxi",
      '    dec_6wp6qxi -->|"Sim"| proc_d9hbj0a',
      '    dec_6wp6qxi -->|"Não"| proc_apf5m3k',
      "    proc_apf5m3k --> proc_41s5v2a",
      "    proc_d9hbj0a --> dec_cxqw47f",
      '    dec_cxqw47f -->|"Sim"| end_37zuxy5',
      '    dec_cxqw47f -->|"Não"| proc_d9hbj0a',
    ].join("\n");

    const imported = mermaidToFlowchart(code);
    expect(imported.lanes).toHaveLength(2);
    expect(imported.nodes).toHaveLength(9);
    expect(imported.edges).toHaveLength(10);

    const comercialLaneId = imported.lanes?.[0]?.id;
    const engenhariaLaneId = imported.lanes?.[1]?.id;
    expect(imported.nodes.find((node) => node.id === "proc_apf5m3k")?.lane_id).toBe(comercialLaneId);
    expect(imported.nodes.find((node) => node.id === "proc_41s5v2a")?.lane_id).toBe(engenhariaLaneId);

    const laidOut = autoLayoutFlowchart(withNormalizedLanes(imported));
    const validar = laidOut.nodes.find((node) => node.id === "proc_41s5v2a");
    const gatewayInfo = laidOut.nodes.find((node) => node.id === "dec_6wp6qxi");
    const solicitar = laidOut.nodes.find((node) => node.id === "proc_apf5m3k");

    expect(validar!.position.x).toBeLessThan(gatewayInfo!.position.x);
    expect(gatewayInfo!.position.x).toBeLessThan(solicitar!.position.x);

    const exported = flowchartToMermaid(laidOut);
    expect(exported).toContain('subgraph lane_lane_e6jo48b ["Comercial"]');
    expect(exported).toContain('dec_6wp6qxi{"Informações<br>completas?"}:::bpmn_decision');
    expect(exported).toContain('dec_6wp6qxi -->|"Não"| proc_apf5m3k');
    expect(exported).toContain('dec_cxqw47f -->|"Não"| proc_d9hbj0a');
  });
});

describe("bpmnMermaidMapping", () => {
  it("expõe classe e linha por tipo", () => {
    expect(bpmnMermaidClassForType("gateway_parallel")).toBe("bpmn_gateway_parallel");
    expect(formatMermaidNodeLine("data", "store", "Base")).toContain('[("Base")]:::bpmn_data');
  });

  it("quebra rótulos longos com br no export Mermaid", () => {
    const line = formatMermaidNodeLine(
      "process",
      "task_a",
      "Registrar oportunidade e anexos no CRM"
    );
    expect(line).toContain("<br>");
  });

  it("monta catálogo para IA", () => {
    const catalog = buildBpmnCatalogForApi();
    expect(catalog.format).toBe("transformometro_bpmn_catalog_v1");
    expect(catalog.node_types.length).toBeGreaterThan(50);
    expect(catalog.ai_guidance.minimal_example).toContain(":::bpmn_");
  });
});
