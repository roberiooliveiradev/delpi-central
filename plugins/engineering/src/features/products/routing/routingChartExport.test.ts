import { describe, expect, it } from "vitest";

import {
  buildOpsTimeExportPayload,
  buildOpsVsTaktExportPayload,
  buildSimDistributionExportPayload,
  type RoutingChartContext,
} from "./routingChartExport";

const ctx: RoutingChartContext = {
  productCode: "90264302",
  branch: "01",
  stageLabel: "Estágio 1",
  scenarioLabel: "Cenário A",
  unit: "s",
};

describe("routingChartExport — contexto e proveniência", () => {
  it("G01 exporta produto/filial/estágio/cenário/unidade com OBSERVED", () => {
    const payload = buildOpsTimeExportPayload(
      ctx,
      [
        {
          operation: "010",
          workCenter: "CT-01",
          description: "Corte",
          time: 12.5,
        },
        { operation: "020", workCenter: "CT-02", time: null },
      ],
      1,
    );
    expect(payload.title).toContain("90264302");
    expect(payload.title).toContain("s");
    const keys = payload.columns.map((c) => c.key);
    for (const key of [
      "produto",
      "filial",
      "estagio",
      "cenario",
      "operacao",
      "ct",
      "tempo",
      "proveniencia",
    ]) {
      expect(keys).toContain(key);
    }
    expect(payload.rows[0]).toMatchObject({
      produto: "90264302",
      filial: "01",
      estagio: "Estágio 1",
      cenario: "Cenário A",
      operacao: "010",
      proveniencia: "OBSERVED",
    });
    expect(payload.rows[1].tempo).toBe("—");
  });

  it("G02 marca acima do takt e mantém unidade consistente", () => {
    const payload = buildOpsVsTaktExportPayload(
      ctx,
      [
        { operation: "010", workCenter: "CT-01", time: 30, overTakt: true },
        { operation: "020", workCenter: "CT-02", time: 10, overTakt: false },
      ],
      20,
      0,
    );
    expect(payload.rows[0].acimaTakt).toBe("Sim");
    expect(payload.rows[1].acimaTakt).toBe("Não");
    expect(payload.rows[0].takt).toBe("20");
    expect(payload.rows[0].proveniencia).toBe("OBSERVED + CALCULATED");
    expect(String(payload.columns.find((c) => c.key === "takt")?.label)).toContain(
      "(s)",
    );
  });

  it("G03 rotula SIMULATION e preserva operações atribuídas", () => {
    const payload = buildSimDistributionExportPayload(
      ctx,
      [
        { station: "Posto 1", load: 45, operations: "010, 020" },
        { station: "Posto 2", load: null },
      ],
      1,
    );
    expect(payload.rows[0]).toMatchObject({
      posto: "Posto 1",
      operacoes: "010, 020",
      proveniencia: "SIMULATION",
    });
    expect(payload.rows[1].carga).toBe("—");
    expect(payload.rows[1].operacoes).toBe("—");
  });

  it("omite a coluna de cenário quando não há cenário ativo", () => {
    const noScenario = { ...ctx, scenarioLabel: null };
    const payload = buildOpsTimeExportPayload(
      noScenario,
      [{ operation: "010", workCenter: "CT-01", time: 1 }],
      1,
    );
    expect(payload.columns.map((c) => c.key)).not.toContain("cenario");
    expect(payload.rows[0]).not.toHaveProperty("cenario");
  });
});
