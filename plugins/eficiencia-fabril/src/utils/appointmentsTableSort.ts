import { isProductionEfficiencyOutlier } from "../constants/businessRules";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";

export type AppointmentsSortColumn =
  | "data_producao"
  | "hora_inicio"
  | "hora_final"
  | "qtd_apontada"
  | "filial"
  | "op"
  | "descricao_produto"
  | "centro_trabalho"
  | "operador"
  | "eficiencia_percentual"
  | "resultado_mod"
  | "status";

export type SortDirection = "asc" | "desc";

export const DEFAULT_APPOINTMENTS_SORT: {
  sortBy: AppointmentsSortColumn;
  sortDir: SortDirection;
} = {
  sortBy: "data_producao",
  sortDir: "desc",
};

function readOperator(item: EficienciaFabrilItem): string {
  return item.nome_operador ?? item.login_operador ?? item.cod_operador ?? "";
}

function readProductDescription(item: EficienciaFabrilItem): string {
  return item.descricao_produto?.trim() || item.produto || "";
}

function readStatusRank(item: EficienciaFabrilItem): number {
  return isProductionEfficiencyOutlier(item.eficiencia_percentual) ? 1 : 0;
}

function compareText(left: string, right: string): number {
  return left.localeCompare(right, "pt-BR", { sensitivity: "base", numeric: true });
}

function compareNullableNumber(
  left: number | null | undefined,
  right: number | null | undefined
): number {
  const a = left ?? Number.NEGATIVE_INFINITY;
  const b = right ?? Number.NEGATIVE_INFINITY;
  return a - b;
}

function compareItem(
  left: EficienciaFabrilItem,
  right: EficienciaFabrilItem,
  sortBy: AppointmentsSortColumn
): number {
  switch (sortBy) {
    case "data_producao":
      return compareText(left.data_producao ?? "", right.data_producao ?? "");
    case "hora_inicio":
      return compareText(left.hora_inicio ?? "", right.hora_inicio ?? "");
    case "hora_final":
      return compareText(left.hora_final ?? "", right.hora_final ?? "");
    case "qtd_apontada":
      return compareNullableNumber(left.qtd_apontada, right.qtd_apontada);
    case "filial":
      return compareText(left.filial ?? "", right.filial ?? "");
    case "op":
      return compareText(left.op ?? "", right.op ?? "");
    case "descricao_produto":
      return compareText(readProductDescription(left), readProductDescription(right));
    case "centro_trabalho":
      return compareText(left.centro_trabalho ?? "", right.centro_trabalho ?? "");
    case "operador":
      return compareText(readOperator(left), readOperator(right));
    case "eficiencia_percentual":
      return compareNullableNumber(left.eficiencia_percentual, right.eficiencia_percentual);
    case "resultado_mod":
      return compareNullableNumber(left.resultado_mod, right.resultado_mod);
    case "status":
      return readStatusRank(left) - readStatusRank(right);
    default:
      return 0;
  }
}

export function sortAppointments(
  items: EficienciaFabrilItem[],
  sortBy: AppointmentsSortColumn,
  sortDir: SortDirection
): EficienciaFabrilItem[] {
  const sorted = [...items].sort((left, right) => compareItem(left, right, sortBy));
  return sortDir === "asc" ? sorted : sorted.reverse();
}

export function toggleSort(
  currentBy: AppointmentsSortColumn,
  currentDir: SortDirection,
  nextBy: AppointmentsSortColumn
): { sortBy: AppointmentsSortColumn; sortDir: SortDirection } {
  if (currentBy !== nextBy) {
    return { sortBy: nextBy, sortDir: "asc" };
  }
  return {
    sortBy: nextBy,
    sortDir: currentDir === "asc" ? "desc" : "asc",
  };
}
