import type { ImpactEffortPoint } from "@delpi/plugin-ui";

import type { MatrizImpactoPonto } from "../data/api/transformometroMatrixApi";

export function matrizPontoToImpactEffortPoint(ponto: MatrizImpactoPonto): ImpactEffortPoint {
  return {
    id: ponto.revisao_id,
    label: ponto.label,
    impacto: ponto.impacto,
    esforco: ponto.esforco,
    quadrante: ponto.quadrante,
    confianca: ponto.confianca,
    revisaoAtiva: ponto.revisao_ativa,
    muted: !ponto.incluir_na_matriz || ponto.cenario_tipo === "baseline",
  };
}

export function sortMatrizPontosForRanking(pontos: MatrizImpactoPonto[]): MatrizImpactoPonto[] {
  return [...pontos].sort((left, right) => {
    if (left.cenario_tipo === "baseline" && right.cenario_tipo !== "baseline") return 1;
    if (right.cenario_tipo === "baseline" && left.cenario_tipo !== "baseline") return -1;
    if (left.incluir_na_matriz !== right.incluir_na_matriz) {
      return left.incluir_na_matriz ? -1 : 1;
    }
    if (right.impacto !== left.impacto) return right.impacto - left.impacto;
    return left.esforco - right.esforco;
  });
}
