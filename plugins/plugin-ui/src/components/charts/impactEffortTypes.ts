/** Quadrante da matriz impacto × esforço (Playbook 21 Transformômetro). */
export type ImpactEffortQuadrant = "quick_win" | "strategic" | "fill_in" | "rethink";

export type ImpactEffortConfidence = "alta" | "media" | "baixa" | "indisponivel";

export type ImpactEffortMatrixMode = "auto" | "manual" | "hibrido";

/** Ponto renderizável no scatter (API ou mock). */
export type ImpactEffortPoint = {
  id: string;
  label: string;
  impacto: number;
  esforco: number;
  quadrante?: ImpactEffortQuadrant;
  confianca?: ImpactEffortConfidence;
  revisaoAtiva?: boolean;
  /** Ex.: baseline — estilo secundário, não clicável */
  muted?: boolean;
  /** Cor de destaque opcional (ex.: série por melhoria no processo). */
  accentColor?: string;
};

export type ImpactEffortQuadrantLabels = Record<ImpactEffortQuadrant, string>;

export const DEFAULT_IMPACT_EFFORT_QUADRANT_LABELS: ImpactEffortQuadrantLabels = {
  quick_win: "Ganhos rápidos",
  strategic: "Estratégicos",
  fill_in: "Complementares",
  rethink: "Reavaliar",
};

export type ImpactEffortAxisLabels = {
  impacto: string;
  esforco: string;
};

export const DEFAULT_IMPACT_EFFORT_AXIS_LABELS: ImpactEffortAxisLabels = {
  impacto: "Impacto",
  esforco: "Esforço",
};

export function resolveImpactEffortQuadrant(
  impacto: number,
  esforco: number,
  threshold = 50,
): ImpactEffortQuadrant {
  const highImpact = impacto >= threshold;
  const highEffort = esforco >= threshold;
  if (highImpact && !highEffort) return "quick_win";
  if (highImpact && highEffort) return "strategic";
  if (!highImpact && !highEffort) return "fill_in";
  return "rethink";
}

export function clampImpactEffortScore(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, value));
}
