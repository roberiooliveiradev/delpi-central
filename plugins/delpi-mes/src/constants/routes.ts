export const BASE_PATH = "/apps/delpi-mes";

export type DelpiMesArea = "monitoring" | "downtimes" | "history";

export const AREAS: Array<{
  id: DelpiMesArea;
  label: string;
  permission: string;
}> = [
  { id: "monitoring", label: "Monitoramento", permission: "delpi-mes.monitoring.view" },
  { id: "downtimes", label: "Paradas", permission: "delpi-mes.downtimes.view" },
  { id: "history", label: "Histórico", permission: "delpi-mes.history.view" },
];

export const BRANCH_PERMISSIONS = {
  "01": "delpi-mes.view.filial-01",
  "02": "delpi-mes.view.filial-02",
} as const;

export type BranchCode = keyof typeof BRANCH_PERMISSIONS;
