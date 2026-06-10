import type { PortalTourStatus } from "../../../data/coreApi";

export const PORTAL_TOUR_STATUS_LABELS: Record<PortalTourStatus | "all", string> = {
  all: "Todos",
  exploring: "Explorando",
  completed: "Concluiu",
  dismissed: "Pulou",
};

export type PortalTourStatusFilter = PortalTourStatus | "all";

export const PORTAL_TOUR_STATUS_FILTERS: PortalTourStatusFilter[] = [
  "all",
  "exploring",
  "completed",
  "dismissed",
];
