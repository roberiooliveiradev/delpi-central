import type { MesPerformance } from "../types/mes";

const PERCENT = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const CYCLE = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const PIECES = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

export function formatPerformancePercent(value: number | null | undefined): string {
  return value == null ? "—" : PERCENT.format(value) + "%";
}

export function formatCycleSeconds(value: number | null | undefined): string {
  return value == null ? "—" : CYCLE.format(value) + " s";
}

export function formatPiecesPerHour(value: number | null | undefined): string {
  return value == null ? "—" : PIECES.format(Math.round(value)) + " pç/h";
}

/** Abaixo deste valor o percentual do run atual fica em vermelho forte. 90% não entra. */
export const LOW_PERFORMANCE_PERCENT = 90;

export function isLowPerformance(percent: number | null | undefined): boolean {
  return percent != null && percent < LOW_PERFORMANCE_PERCENT;
}

/** Comparação factual com o ritmo padrão — sem faixas inventadas. */
export function performancePaceLabel(percent: number | null | undefined): string | null {
  if (percent == null) return null;
  const shown = Math.round(percent * 10) / 10;
  if (shown > 100) return "Acima do ritmo padrão";
  if (shown === 100) return "No ritmo padrão";
  return "Abaixo do ritmo padrão";
}

export type PerformanceQualityHint = { short: string; detail: string };

const QUALITY_MESSAGES: Record<string, PerformanceQualityHint> = {
  standard_time_unavailable: {
    short: "Indisponível",
    detail: "Tempo padrão não disponível para esta operação.",
  },
  piece_conversion_unavailable: {
    short: "Indisponível",
    detail: "Não foi possível converter a unidade da operação para peças.",
  },
  upstream_unavailable: {
    short: "Indisponível",
    detail: "O tempo padrão não estava disponível quando a produção foi iniciada.",
  },
  insufficient_count_data: {
    short: "Aguardando produção",
    detail: "Aguardando peças produzidas para calcular a Performance.",
  },
  insufficient_producing_time: {
    short: "Aguardando produção",
    detail: "Aguardando tempo de produção suficiente para calcular a Performance.",
  },
  invalid_standard_time_snapshot: {
    short: "Indisponível",
    detail: "O tempo padrão registrado para esta produção é inválido.",
  },
};

/** null quando a qualidade é "complete" — não ocupa espaço na UI. */
export function performanceQualityHint(quality: string | null | undefined): PerformanceQualityHint | null {
  if (!quality || quality === "complete") return null;
  return QUALITY_MESSAGES[quality] ?? { short: "Indisponível", detail: "Dados de Performance indisponíveis no momento." };
}

const SOURCE_LABELS: Record<string, string> = {
  shy_tempad: "Padrão da ordem de produção",
  shy_tempom_quant: "Padrão calculado da ordem de produção",
  sg2_tempad: "Padrão do roteiro",
};

export function standardTimeSourceLabel(source: string | null | undefined): string {
  if (!source) return "Não disponível";
  return SOURCE_LABELS[source] ?? "Tempo padrão registrado";
}

export const PERFORMANCE_HELP =
  "Compara o tempo padrão necessário para produzir as peças com o tempo em que o posto esteve efetivamente produzindo. " +
  "Paradas, pausas e setup não entram neste cálculo. " +
  "Valores acima de 100% indicam ritmo superior ao tempo padrão registrado.";

export const ACTUAL_CYCLE_HELP =
  "Tempo médio efetivamente utilizado por peça durante os períodos em que o posto esteve produzindo.";

export type { MesPerformance };
