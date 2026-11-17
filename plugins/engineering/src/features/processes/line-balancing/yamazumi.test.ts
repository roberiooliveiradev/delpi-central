import { describe, expect, it } from "vitest";

import type { HypotheticalPost } from "../../products/routing/routingStudyDraft";
import type { RoutingOperationView } from "../../products/routing/routingGrouping";
import {
  AGGREGATE_TIME_CATEGORY,
  assignOperationToPost,
  buildYamazumiChartSpec,
  buildYamazumiExportRows,
  computePostLoads,
  unassignedOperations,
} from "./yamazumi";

function op(
  key: string,
  code: string,
  time: number | null,
): RoutingOperationView {
  return {
    key,
    operation_code: code,
    operation_description: `Op ${code}`,
    work_center: "CT-1",
    resource_code: "RES-1",
    operation_type: null,
    mandatory_operation: null,
    mandatory_sequence: null,
    mandatory_report: null,
    time_minutes_piece: time,
    setup_hours: null,
    components: [],
    source_rows: [],
  };
}

function post(id: string, refs: string[]): HypotheticalPost {
  return {
    clientId: id,
    name: id.toUpperCase(),
    operationRefs: refs,
    operators: null,
    parallelPositions: null,
    note: "",
  };
}

describe("computePostLoads", () => {
  it("soma tempos por peça das operações atribuídas", () => {
    const ops = [op("a", "01", 1.5), op("b", "02", 2), op("c", "03", 0.5)];
    const loads = computePostLoads([post("p1", ["a", "b"]), post("p2", ["c"])], ops);
    expect(loads[0].loadMinutes).toBe(3.5);
    expect(loads[1].loadMinutes).toBe(0.5);
  });

  it("tempo ausente é UNKNOWN — nunca somado como zero", () => {
    const ops = [op("a", "01", null), op("b", "02", 1)];
    const [load] = computePostLoads([post("p1", ["a", "b"])], ops);
    expect(load.loadMinutes).toBe(1);
    expect(load.unknownOps.map((o) => o.key)).toEqual(["a"]);
  });

  it("posto sem tempo algum tem carga null (não zero fictício)", () => {
    const ops = [op("a", "01", null)];
    const [load] = computePostLoads([post("p1", ["a"])], ops);
    expect(load.loadMinutes).toBeNull();
    expect(load.empty).toBe(false);
  });

  it("posto vazio é marcado, sem carga", () => {
    const [load] = computePostLoads([post("p1", [])], [op("a", "01", 1)]);
    expect(load.empty).toBe(true);
    expect(load.loadMinutes).toBeNull();
  });

  it("referência para operação inexistente é ignorada", () => {
    const [load] = computePostLoads([post("p1", ["ghost"])], []);
    expect(load.empty).toBe(true);
  });
});

describe("unassignedOperations", () => {
  it("lista operações fora de qualquer posto", () => {
    const ops = [op("a", "01", 1), op("b", "02", 2), op("c", "03", 3)];
    const unassigned = unassignedOperations(
      [post("p1", ["a"]), post("p2", ["b"])],
      ops,
    );
    expect(unassigned.map((o) => o.key)).toEqual(["c"]);
  });
});

describe("assignOperationToPost", () => {
  const posts = [post("p1", ["a"]), post("p2", ["b"])];

  it("atribui operação livre ao posto alvo", () => {
    const updates = assignOperationToPost(posts, "c", "p1");
    expect(updates).toEqual([
      { postId: "p1", patch: { operationRefs: ["a", "c"] } },
    ]);
  });

  it("move operação entre postos sem duplicar carga (política exclusiva)", () => {
    const updates = assignOperationToPost(posts, "a", "p2");
    expect(updates).toEqual([
      { postId: "p1", patch: { operationRefs: [] } },
      { postId: "p2", patch: { operationRefs: ["b", "a"] } },
    ]);
  });

  it("não duplica quando a operação já está no posto alvo", () => {
    expect(assignOperationToPost(posts, "a", "p1")).toEqual([]);
  });
});

describe("buildYamazumiChartSpec", () => {
  it("empilha um segmento por operação e adiciona a linha de takt", () => {
    const ops = [op("a", "01", 1), op("b", "02", 2)];
    const loads = computePostLoads(
      [post("p1", ["a", "b"]), post("p2", [])],
      ops,
    );
    const spec = buildYamazumiChartSpec(loads, 1.5);
    expect(spec.rows).toHaveLength(2);
    expect(spec.rows[0].op_a).toBe(1);
    expect(spec.rows[0].op_b).toBe(2);
    expect(spec.rows[0].takt).toBe(1.5);
    expect(spec.rows[1].op_a).toBe(0);
    expect(spec.series).toHaveLength(3);
    expect(spec.series[2]).toMatchObject({
      dataKey: "takt",
      plotAs: "line",
    });
  });

  it("sem takt não emite série de referência", () => {
    const loads = computePostLoads([post("p1", ["a"])], [op("a", "01", 1)]);
    const spec = buildYamazumiChartSpec(loads, null);
    expect(spec.series).toHaveLength(1);
    expect(spec.rows[0].takt).toBeUndefined();
  });

  it("categoria única honesta de tempo agregado", () => {
    expect(AGGREGATE_TIME_CATEGORY).toContain("composição desconhecida");
  });
});

describe("buildYamazumiExportRows", () => {
  it("inclui postos, não atribuídas e proveniência por linha", () => {
    const ops = [op("a", "01", 1), op("b", "02", null), op("c", "03", 2)];
    const loads = computePostLoads([post("p1", ["a", "b"])], ops);
    const rows = buildYamazumiExportRows(
      loads,
      unassignedOperations([post("p1", ["a", "b"])], ops),
    );
    expect(rows).toHaveLength(3);
    expect(rows[0].provenance).toBe("OBSERVED+DRAFT_LOCAL");
    expect(rows[1].time_minutes_piece).toBe("UNKNOWN");
    expect(rows[2].post).toBe("(não atribuída)");
    expect(rows[2].provenance).toContain("não atribuída");
  });
});
