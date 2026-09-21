import type { DashboardViewMode, FilialOption, SetorOption } from "../data/api/transformometroApi";

export const CONSOLIDATED_UNIT_CONTEXT = "Consolidado (todas as unidades)";

export function formatDashboardPeriodLabel(dataInicial: string, dataFinal: string): string {
  const start = dataInicial.split("-").reverse().join("/");
  const end = dataFinal.split("-").reverse().join("/");
  return `${start} — ${end}`;
}

function resolveFilialLabel(id: string, filiais: readonly FilialOption[]): string {
  const found = filiais.find(
    (item) => item.id === id || item.filial_id === id || item.codigo_filial === id,
  );
  const label = found?.label?.trim();
  return label || id;
}

function resolveSetorLabel(id: string, setores: readonly SetorOption[]): string {
  const found = setores.find((item) => item.id === id || item.setor_id === id || item.codigo_setor === id);
  const label = found?.label?.trim();
  return label || id;
}

export function buildDashboardKpiContextLabel(input: {
  viewMode: DashboardViewMode;
  filialIds: readonly string[];
  setorIds?: readonly string[];
  periodLabel: string;
  filiais?: readonly FilialOption[];
  setores?: readonly SetorOption[];
}): string {
  const period = input.periodLabel.trim();
  const filiais = input.filiais ?? [];
  const setores = input.setores ?? [];

  if (input.viewMode === "consolidated") {
    return period ? `${CONSOLIDATED_UNIT_CONTEXT} · ${period}` : CONSOLIDATED_UNIT_CONTEXT;
  }

  const unitLabels = input.filialIds
    .map((id) => resolveFilialLabel(id, filiais))
    .filter(Boolean);
  const departmentLabels = (input.setorIds ?? [])
    .map((id) => resolveSetorLabel(id, setores))
    .filter(Boolean);

  const parts =
    input.viewMode === "department"
      ? [...departmentLabels, ...unitLabels]
      : unitLabels;

  const scope = parts.join(" · ");
  if (scope && period) return `${scope} · ${period}`;
  return scope || period;
}
