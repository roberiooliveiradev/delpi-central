import type { OverviewTemporalNature } from "../../api/overview";

export const OVERVIEW_CONTENT = {
  title: "Visão geral",
  eyebrow: "Portal Suprimentos",
  description:
    "Indicadores do período no seu escopo. O Início é para ação e descoberta — não use a Visão geral como fila operacional.",
  helpAriaLabel: "Ajuda: Visão geral e natureza temporal",
  branchAll: "Todas as liberadas",
  branchLabel: "Filial",
  periodFromLabel: "De",
  periodToLabel: "Até",
  reloadLabel: "Atualizar",
  loading: "Carregando indicadores…",
  error: "Não foi possível carregar a Visão geral.",
  empty: "Nenhum indicador disponível para este recorte.",
  unavailable: "Indisponível",
  partialNote: "Alguns indicadores falharam; o restante permanece utilizável.",
  temporalLabels: {
    interval: "Intervalo",
    snapshot: "Snapshot",
    state: "Estado atual",
  } satisfies Record<OverviewTemporalNature, string>,
} as const;

export function firstDayOfMonthIso(today = new Date()): string {
  const y = today.getFullYear();
  const m = String(today.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}-01`;
}

export function todayIso(today = new Date()): string {
  const y = today.getFullYear();
  const m = String(today.getMonth() + 1).padStart(2, "0");
  const d = String(today.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function temporalNatureLabel(nature: OverviewTemporalNature): string {
  return OVERVIEW_CONTENT.temporalLabels[nature];
}
