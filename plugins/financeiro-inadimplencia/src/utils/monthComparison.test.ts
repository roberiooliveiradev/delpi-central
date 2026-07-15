import { describe, expect, it } from "vitest";

import type { InadimplenciaMensalItem } from "../types/inadimplencia";
import {
  comparePontualidadeQtd,
  resolveMonthComparison,
} from "./monthComparison";

function item(anoMes: string, percentual: number): InadimplenciaMensalItem {
  return {
    mes: `${anoMes}-01`,
    ano_mes: anoMes,
    total_titulos: 100,
    titulos_em_dia: 90,
    titulos_atraso: 10,
    valor_total: 1000,
    valor_em_dia: 900,
    valor_atraso: 100,
    percentual_em_dia_qtd: percentual,
    percentual_em_dia_valor: percentual,
  };
}

describe("resolveMonthComparison", () => {
  it("pega o mês corrente e o anterior da série", () => {
    const items = [item("2026-05", 90), item("2026-06", 91), item("2026-07", 92)];
    const result = resolveMonthComparison(items, new Date(2026, 6, 15));
    expect(result.current?.ano_mes).toBe("2026-07");
    expect(result.previous?.ano_mes).toBe("2026-06");
  });

  it("usa o último mês disponível quando o corrente não veio na série", () => {
    const items = [item("2026-05", 90), item("2026-06", 91)];
    const result = resolveMonthComparison(items, new Date(2026, 6, 15));
    expect(result.current?.ano_mes).toBe("2026-06");
    expect(result.previous?.ano_mes).toBe("2026-05");
  });
});

describe("comparePontualidadeQtd", () => {
  it("classifica melhor, pior e estável", () => {
    expect(comparePontualidadeQtd(92, 90).trend).toBe("melhor");
    expect(comparePontualidadeQtd(88, 90).trend).toBe("pior");
    expect(comparePontualidadeQtd(90, 90).trend).toBe("estavel");
  });
});
