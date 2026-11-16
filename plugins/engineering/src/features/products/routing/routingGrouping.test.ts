/** Consolidação visual do roteiro — a mesma identidade oficial do
 * domínio EVA (produto × nível × operação × CT × recurso); os números
 * de análise em si jamais são computados aqui. */

import { describe, expect, it } from "vitest";

import {
  formatMinutes,
  groupRoutingRows,
  stageLabel,
} from "./routingGrouping";
import type { ProductRoutingRow } from "../types";

function row(partial: Partial<ProductRoutingRow>): ProductRoutingRow {
  return {
    product_code: "90264302",
    bom_level: 0,
    operation_code: "010",
    work_center: "CT10",
    resource_code: "LASER01",
    branch: "01",
    route_code: "01",
    ...partial,
  };
}

describe("groupRoutingRows — dedup pela identidade oficial", () => {
  it("funde linhas repetidas por componente na mesma operação", () => {
    const g = groupRoutingRows([
      row({ component_code: "A1", component_sequence: "010" }),
      row({ component_code: "A2", component_sequence: "020" }),
      row({ component_code: "A3", component_sequence: "030" }),
    ]);
    expect(g.rows_total).toBe(3);
    expect(g.unique_operations).toBe(1);
    expect(g.stages).toHaveLength(1);
    const op = g.stages[0].operations[0];
    expect(op.components.map((c) => c.code)).toEqual(["A1", "A2", "A3"]);
    expect(op.source_rows).toBe(3);
  });

  it("componente repetido não duplica na operação", () => {
    const g = groupRoutingRows([
      row({ component_code: "A1" }),
      row({ component_code: "A1" }),
    ]);
    expect(g.stages[0].operations[0].components).toHaveLength(1);
  });

  it("mesmo código de operação em outro nível vira estágio separado", () => {
    const g = groupRoutingRows([
      row({ bom_level: 0 }),
      row({ bom_level: 1, product_code: "SUB-1" }),
    ]);
    expect(g.stages).toHaveLength(2);
    expect(g.stages.map((s) => s.bom_level)).toEqual([0, 1]);
  });

  it("CT ou recurso diferente não funde a operação", () => {
    const g = groupRoutingRows([
      row({ work_center: "CT10" }),
      row({ work_center: "CT20" }),
      row({ resource_code: "OUTRO" }),
    ]);
    expect(g.stages[0].operations).toHaveLength(3);
  });

  it("linha sem componente ainda conta como linha de origem", () => {
    const g = groupRoutingRows([row({ component_code: null })]);
    const op = g.stages[0].operations[0];
    expect(op.components).toHaveLength(0);
    expect(op.source_rows).toBe(1);
  });

  it("entrada vazia produz estágios vazios (estado honesto)", () => {
    const g = groupRoutingRows([]);
    expect(g.stages).toHaveLength(0);
    expect(g.unique_operations).toBe(0);
  });

  it("preserva tempos e flags sem conversão", () => {
    const g = groupRoutingRows([
      row({
        standard_time_minutes_piece: 1.234567,
        setup_hours: 0.5,
        operation_type: "1",
        mandatory_operation: "S",
      }),
    ]);
    const op = g.stages[0].operations[0];
    expect(op.time_minutes_piece).toBe(1.234567);
    expect(op.setup_hours).toBe(0.5);
    expect(op.operation_type).toBe("1");
    expect(op.mandatory_operation).toBe("S");
  });
});

describe("rótulos e formatação", () => {
  it("stageLabel identifica nível e produto", () => {
    const g = groupRoutingRows([row({ bom_level: 2, product_code: "X" })]);
    expect(stageLabel(g.stages[0])).toBe("Estágio 2 — X");
  });

  it("formatMinutes preserva o valor e exibe unidade", () => {
    expect(formatMinutes(1.5)).toContain("min");
    expect(formatMinutes(null)).toBe("—");
  });
});
