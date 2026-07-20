import { describe, expect, it } from "vitest";
import {
  collectComparativoAvisos,
  collectComparativoCategorias,
} from "./revisaoComparativoChart";
import { medicaoCategoriaHints } from "../content/beneficioCalculoLabels";
import type { ProcessoComparativoItem } from "../data/api/transformometroApi";

function item(partial: Partial<ProcessoComparativoItem>): ProcessoComparativoItem {
  return {
    revisao_id: partial.revisao_id ?? "r1",
    versao_revisao: partial.versao_revisao ?? "2.0.0",
    cenario_tipo: partial.cenario_tipo ?? "melhoria",
    beneficio_calculo_categoria: partial.beneficio_calculo_categoria ?? "economia_tempo",
    totais: {
      economia_bruta: 0,
      economia_liquida_mes: 0,
      horas_economizadas_mes: 0,
      ...(partial.totais ?? {}),
    },
    avisos: partial.avisos,
  };
}

describe("revisaoComparativoChart / beneficio UI helpers", () => {
  it("collectComparativoCategorias ignores baseline and dedupes", () => {
    const cats = collectComparativoCategorias([
      item({ revisao_id: "b", cenario_tipo: "baseline" }),
      item({ revisao_id: "a", beneficio_calculo_categoria: "ganho_capacidade" }),
      item({ revisao_id: "c", beneficio_calculo_categoria: "ganho_capacidade" }),
      item({ revisao_id: "d", beneficio_calculo_categoria: "reducao_volume" }),
    ]);
    expect(cats).toEqual(["ganho_capacidade", "reducao_volume"]);
  });

  it("collectComparativoAvisos flattens messages", () => {
    const avisos = collectComparativoAvisos([
      item({
        versao_revisao: "2.0.0",
        cenario_tipo: "melhoria",
        avisos: [{ code: "x", severity: "capacidade", message: "Volume alto" }],
      }),
    ]);
    expect(avisos).toHaveLength(1);
    expect(avisos[0].message).toContain("Volume alto");
  });

  it("medicaoCategoriaHints adds divergence tip for economia_tempo", () => {
    const hints = medicaoCategoriaHints("economia_tempo", 120, 100);
    expect(hints.length).toBeGreaterThanOrEqual(2);
    expect(hints.some((h) => h.includes("100"))).toBe(true);
  });

  it("medicaoCategoriaHints warns ganho_capacidade when volume not above ref", () => {
    const hints = medicaoCategoriaHints("ganho_capacidade", 90, 100);
    expect(hints.some((h) => h.includes("acima da referência"))).toBe(true);
  });
});
