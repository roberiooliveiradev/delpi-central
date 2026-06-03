const CRITERIO_RATEIO_LABELS: Record<string, string> = {
  igualitario: "Igualitário entre vínculos",
  por_revisoes_ativas: "Por revisões ativas",
  por_peso: "Por peso do vínculo",
};

const BASE_COMPETENCIA_LABELS: Record<string, string> = {
  mensal_cheio: "Mensal cheio",
  proporcional_dias: "Proporcional aos dias",
};

export function labelCriterioRateio(value?: string | null): string {
  if (!value) return "—";
  return CRITERIO_RATEIO_LABELS[value] ?? value;
}

export function labelBaseCompetencia(value?: string | null): string {
  if (!value) return "Mensal cheio";
  return BASE_COMPETENCIA_LABELS[value] ?? value;
}

export function labelSimNao(value: boolean | undefined): string {
  if (value === undefined) return "—";
  return value ? "Sim" : "Não";
}
