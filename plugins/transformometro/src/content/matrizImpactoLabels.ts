import type { ImpactEffortQuadrantLabels } from "@delpi/plugin-ui/index";

import type {
  ImpactEffortConfidence,
  ImpactEffortQuadrant,
  MatrizImpactoPonto,
} from "../data/api/transformometroMatrixApi";

export const MATRIZ_QUADRANTE_LABELS: ImpactEffortQuadrantLabels = {
  quick_win: "Ganho rápido",
  strategic: "Estratégico",
  fill_in: "Complementar",
  rethink: "Reavaliar",
};

/** Rótulos no gráfico (plural, como nos eixos da matriz). */
export const MATRIZ_QUADRANTE_LABELS_GRAFICO: ImpactEffortQuadrantLabels = {
  quick_win: "Ganhos rápidos",
  strategic: "Estratégicos",
  fill_in: "Complementares",
  rethink: "Reavaliar",
};

export const MATRIZ_CONFIANCA_LABELS: Record<ImpactEffortConfidence, string> = {
  alta: "Alta",
  media: "Média",
  baixa: "Baixa",
  indisponivel: "Indisponível",
};

export const MATRIZ_QUADRANTE_BADGE_CLASS: Record<ImpactEffortQuadrant, string> = {
  quick_win: "tm-matrix-badge--quick-win",
  strategic: "tm-matrix-badge--strategic",
  fill_in: "tm-matrix-badge--fill-in",
  rethink: "tm-matrix-badge--rethink",
};

export const MATRIZ_QUADRANTE_BADGE_SHORT: Record<ImpactEffortQuadrant, string> = {
  quick_win: "QW",
  strategic: "EST",
  fill_in: "CMP",
  rethink: "REV",
};

export type ProcessoWorkspaceMatrixBadge = {
  label: string;
  className: string;
  title: string;
};

export function resolveMatrixTreeBadge(input: {
  cenario_tipo?: string | null;
  ponto?: Pick<MatrizImpactoPonto, "impacto" | "esforco" | "quadrante" | "incluir_na_matriz">;
}): ProcessoWorkspaceMatrixBadge | undefined {
  const cenario = String(input.cenario_tipo ?? "").toLowerCase();
  if (cenario === "baseline") {
    return {
      label: "—",
      className: "tm-matrix-badge--neutral",
      title: "Referência (linha de base)",
    };
  }
  const ponto = input.ponto;
  if (!ponto?.incluir_na_matriz) return undefined;
  return {
    label: MATRIZ_QUADRANTE_BADGE_SHORT[ponto.quadrante],
    className: MATRIZ_QUADRANTE_BADGE_CLASS[ponto.quadrante],
    title: `Impacto ${ponto.impacto.toLocaleString("pt-BR")} · Esforço ${ponto.esforco.toLocaleString("pt-BR")} · ${MATRIZ_QUADRANTE_LABELS[ponto.quadrante]}`,
  };
}
