import type { ImpactEffortQuadrantLabels } from "@delpi/plugin-ui";

import type { ImpactEffortConfidence, ImpactEffortQuadrant } from "../data/api/transformometroMatrixApi";

export const MATRIZ_QUADRANTE_LABELS: ImpactEffortQuadrantLabels = {
  quick_win: "Quick win",
  strategic: "Estratégico",
  fill_in: "Complementar",
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
