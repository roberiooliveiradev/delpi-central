import { DELPI_MES_DOWNTIME_REASONS_MANAGE } from "./permissions";

export const BASE_PATH = "/apps/delpi-mes";

export type DelpiMesArea = "monitoring" | "downtimes" | "history" | "registrations";

export const AREAS: Array<{
  id: DelpiMesArea;
  label: string;
  permission: string;
  /** Áreas globais não são escopadas por filial (ex.: catálogos compartilhados). */
  global?: boolean;
}> = [
  { id: "monitoring", label: "Monitoramento", permission: "delpi-mes.monitoring.view" },
  { id: "downtimes", label: "Paradas", permission: "delpi-mes.downtimes.view" },
  { id: "history", label: "Histórico", permission: "delpi-mes.history.view" },
  { id: "registrations", label: "Cadastros", permission: DELPI_MES_DOWNTIME_REASONS_MANAGE, global: true },
];

export function isGlobalArea(area: DelpiMesArea | undefined): boolean {
  return AREAS.some((entry) => entry.id === area && entry.global);
}

export const BRANCH_PERMISSIONS = {
  "01": "delpi-mes.view.filial-01",
  "02": "delpi-mes.view.filial-02",
} as const;

export type BranchCode = keyof typeof BRANCH_PERMISSIONS;
