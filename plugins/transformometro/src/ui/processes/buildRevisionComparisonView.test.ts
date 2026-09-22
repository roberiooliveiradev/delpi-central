import { describe, expect, it } from "vitest";

import type { Medicao, ProcessoInstancia, Revisao } from "../../data/api/transformometroApi";
import {
  buildMeasurementComparisonRows,
  buildRevisionComparisonView,
  filterComparativoByRevisoes,
  isBaselineCenario,
  provenanceForRevisionRole,
} from "./buildRevisionComparisonView";

function instancia(id: string): ProcessoInstancia {
  return {
    instancia_id: id,
    processo_id: "p1",
    rotulo_instancia: `Melhoria ${id}`,
  };
}

function revisao(
  id: string,
  instanciaId: string,
  opts: Partial<Revisao> = {},
): Revisao {
  return {
    revisao_id: id,
    processo_id: "p1",
    instancia_id: instanciaId,
    versao_revisao: id,
    cenario_tipo: opts.cenario_tipo ?? "melhoria",
    revisao_referencia_id: opts.revisao_referencia_id ?? null,
    data_inicio_vigencia: "2026-01-01",
    revisao_ativa: opts.revisao_ativa ?? false,
    ...opts,
  };
}

describe("buildRevisionComparisonView — reference resolution", () => {
  it("CASE I: múltiplas instâncias exigem seleção explícita (nunca instances[0])", () => {
    const view = buildRevisionComparisonView({
      processId: "p1",
      instancias: [instancia("A"), instancia("B")],
      revisoes: [revisao("R1", "A", { cenario_tipo: "baseline" })],
      selectedInstanciaId: null,
      selectedRevisaoId: null,
    });
    expect(view.mode).toBe("needs_instance_selection");
    expect(view.instanceId).toBeNull();
  });

  it("CASE J: instância única resolve sem seleção", () => {
    const view = buildRevisionComparisonView({
      processId: "p1",
      instancias: [instancia("A")],
      revisoes: [revisao("R1", "A", { cenario_tipo: "baseline" })],
      selectedInstanciaId: null,
      selectedRevisaoId: null,
    });
    expect(view.mode).toBe("baseline_only");
    expect(view.instanceId).toBe("A");
    expect(view.asIs?.revisao_id).toBe("R1");
  });

  it("CASE A: baseline only — TO-BE cenário ausente", () => {
    const view = buildRevisionComparisonView({
      processId: "p1",
      instancias: [instancia("A")],
      revisoes: [revisao("R1", "A", { cenario_tipo: "baseline" })],
      selectedInstanciaId: null,
      selectedRevisaoId: null,
    });
    expect(view.mode).toBe("baseline_only");
    expect(view.asIs?.revisao_id).toBe("R1");
    expect(view.toBe?.revisao_id).toBe("R1");
    expect(view.referenceRevisionId).toBeNull();
  });

  it("CASE K/B: R3 referencia R1 — AS-IS=R1 TO-BE=R3 nunca R2", () => {
    const view = buildRevisionComparisonView({
      processId: "p1",
      instancias: [instancia("A")],
      revisoes: [
        revisao("R1", "A", { cenario_tipo: "baseline" }),
        revisao("R2", "A", { cenario_tipo: "melhoria", revisao_referencia_id: "R1" }),
        revisao("R3", "A", { cenario_tipo: "automacao", revisao_referencia_id: "R1" }),
      ],
      selectedInstanciaId: null,
      selectedRevisaoId: "R3",
    });
    expect(view.mode).toBe("pair");
    expect(view.asIs?.revisao_id).toBe("R1");
    expect(view.toBe?.revisao_id).toBe("R3");
    expect(view.referenceRevisionId).toBe("R1");
  });

  it("CASE H: legacy missing reference — sem fallback para previous/active", () => {
    const view = buildRevisionComparisonView({
      processId: "p1",
      instancias: [instancia("A")],
      revisoes: [
        revisao("R1", "A", { cenario_tipo: "baseline" }),
        revisao("R2", "A", { cenario_tipo: "melhoria", revisao_referencia_id: null }),
      ],
      selectedInstanciaId: null,
      selectedRevisaoId: "R2",
    });
    expect(view.mode).toBe("legacy_reference_missing");
    expect(view.asIs).toBeNull();
    expect(view.toBe?.revisao_id).toBe("R2");
  });

  it("CASE T: cross-instance isolation — A/R2 não puxa R5/R6", () => {
    const view = buildRevisionComparisonView({
      processId: "p1",
      instancias: [instancia("A"), instancia("B")],
      revisoes: [
        revisao("R1", "A", { cenario_tipo: "baseline" }),
        revisao("R2", "A", { cenario_tipo: "melhoria", revisao_referencia_id: "R1" }),
        revisao("R5", "B", { cenario_tipo: "baseline" }),
        revisao("R6", "B", { cenario_tipo: "melhoria", revisao_referencia_id: "R5" }),
      ],
      selectedInstanciaId: "A",
      selectedRevisaoId: "R2",
    });
    expect(view.mode).toBe("pair");
    expect(view.asIs?.revisao_id).toBe("R1");
    expect(view.toBe?.revisao_id).toBe("R2");
    expect(view.scopedRevisoes.map((r) => r.revisao_id).sort()).toEqual(["R1", "R2"]);
  });

  it("CASE G: revisão inativa permanece legível no par", () => {
    const view = buildRevisionComparisonView({
      processId: "p1",
      instancias: [instancia("A")],
      revisoes: [
        revisao("R1", "A", { cenario_tipo: "baseline" }),
        revisao("R2", "A", {
          cenario_tipo: "melhoria",
          revisao_referencia_id: "R1",
          revisao_ativa: false,
        }),
      ],
      selectedInstanciaId: null,
      selectedRevisaoId: "R2",
    });
    expect(view.mode).toBe("pair");
    expect(view.toBe?.revisao_ativa).toBe(false);
  });

  it("reference_not_in_scope quando ref aponta fora da instância", () => {
    const view = buildRevisionComparisonView({
      processId: "p1",
      instancias: [instancia("A")],
      revisoes: [
        revisao("R2", "A", { cenario_tipo: "melhoria", revisao_referencia_id: "R99" }),
      ],
      selectedInstanciaId: null,
      selectedRevisaoId: null,
    });
    expect(view.mode).toBe("reference_not_in_scope");
    expect(view.referenceRevisionId).toBe("R99");
    expect(view.asIs).toBeNull();
  });
});

describe("measurement comparison + provenance", () => {
  it("CASE L: delta só com ambos valores — CALCULATED_PRESENTATION", () => {
    const asIs: Medicao = {
      revisao_id: "R1",
      volume_mensal: 100,
      tempo_medio_execucao_min: 10,
      tempo_retrabalho_min: 2,
      percentual_retrabalho: 5,
      percentual_erro: 1,
      quantidade_erros_mes: 3,
      custo_hora_mao_obra: 50,
      custo_unitario_erro: 20,
      custo_unitario_retrabalho: 15,
      custo_outros_desperdicios: 0,
    };
    const toBe: Medicao = { ...asIs, revisao_id: "R2", volume_mensal: 120, tempo_medio_execucao_min: 8 };
    const rows = buildMeasurementComparisonRows(asIs, toBe);
    const volume = rows.find((r) => r.id === "volume_mensal")!;
    expect(volume.asIsValue).toBe(100);
    expect(volume.toBeValue).toBe(120);
    expect(volume.delta).toBe(20);
    expect(volume.deltaKind).toBe("CALCULATED_PRESENTATION");
    const tempo = rows.find((r) => r.id === "tempo_medio_execucao_min")!;
    expect(tempo.delta).toBe(-2);
  });

  it("CASE D: sem medição TO-BE — delta indisponível (não zero)", () => {
    const asIs: Medicao = {
      revisao_id: "R1",
      volume_mensal: 100,
      tempo_medio_execucao_min: 10,
      tempo_retrabalho_min: 0,
      percentual_retrabalho: 0,
      percentual_erro: 0,
      quantidade_erros_mes: 0,
      custo_hora_mao_obra: 0,
      custo_unitario_erro: 0,
      custo_unitario_retrabalho: 0,
      custo_outros_desperdicios: 0,
    };
    const rows = buildMeasurementComparisonRows(asIs, null);
    expect(rows.every((r) => r.toBeValue === null && r.delta === null)).toBe(true);
  });

  it("CASE P: TO-BE cenário = PROPOSTO; baseline AS-IS = INFORMADO", () => {
    expect(
      provenanceForRevisionRole("to_be", revisao("R2", "A", { cenario_tipo: "melhoria" })),
    ).toBe("PROPOSTO");
    expect(
      provenanceForRevisionRole("as_is", revisao("R1", "A", { cenario_tipo: "baseline" })),
    ).toBe("INFORMADO");
  });

  it("filterComparativoByRevisoes não cruza instâncias", () => {
    const scoped = [revisao("R1", "A"), revisao("R2", "A")];
    const items = [
      { revisao_id: "R1", totais: { economia_bruta: 1, economia_liquida_mes: 1, horas_economizadas_mes: 1 } },
      { revisao_id: "R6", totais: { economia_bruta: 9, economia_liquida_mes: 9, horas_economizadas_mes: 9 } },
    ];
    expect(filterComparativoByRevisoes(items as never, scoped).map((i) => i.revisao_id)).toEqual([
      "R1",
    ]);
  });

  it("isBaselineCenario", () => {
    expect(isBaselineCenario("baseline")).toBe(true);
    expect(isBaselineCenario("melhoria")).toBe(false);
  });
});
