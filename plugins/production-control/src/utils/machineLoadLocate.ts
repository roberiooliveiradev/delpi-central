import { copy } from "../content/copy";
import type { MachineLoadLocateJourney, MachineLoadLocateStop, ProductionStatus } from "../types";
import { machineLoadStatusBadge } from "./machineLoadStatus";

/** C2_NUM = 6 primeiros dígitos da chave completa da OP (C2_OP / H8_OP, 11 posições). */
export const CONJUNTO_KEY_LENGTH = 6;

export function conjuntoKeyFromOrder(productionOrder: string | null | undefined): string | null {
  const code = (productionOrder || "").trim().toUpperCase();
  if (code.length < CONJUNTO_KEY_LENGTH) return null;
  return code.slice(0, CONJUNTO_KEY_LENGTH);
}

export function machineLoadLocateRowKey(
  stop: Pick<MachineLoadLocateStop, "production_order" | "operation_code">,
): string {
  return `${stop.production_order}::${stop.operation_code}`;
}

export type LocateProgressStep = {
  tone: "done" | "running" | "queued";
  label: string;
};

/** Resumo visual da jornada: já apontada / em produção / na fila. */
export function locateJourneyProgress(stops: MachineLoadLocateStop[]): LocateProgressStep[] {
  return stops.map((stop) => {
    if (stop.is_in_production || stop.production_status === "in_progress") {
      return { tone: "running", label: copy.machineLoad.status.inProgress };
    }
    if (stop.production_status === "started") {
      return { tone: "done", label: copy.machineLoad.status.started };
    }
    return { tone: "queued", label: copy.machineLoad.status.notStarted };
  });
}

export function locateJourneyTitle(journey: MachineLoadLocateJourney): string {
  // kind "op" = conjunto (C2_NUM, 6 dígitos); kind "pa" = produto acabado.
  if (journey.kind === "op") {
    return copy.machineLoad.locate.journeyConjunto(journey.key);
  }
  return copy.machineLoad.locate.journeyProduct(journey.key);
}

export function locateStopStatusLabel(status: ProductionStatus | string, isInProduction: boolean): string {
  if (isInProduction || status === "in_progress") {
    return machineLoadStatusBadge("in_progress").label;
  }
  return machineLoadStatusBadge(status).label;
}

export function locateStopStatusTone(
  status: ProductionStatus | string,
  isInProduction: boolean,
): "done" | "running" | "queued" {
  if (isInProduction || status === "in_progress") return "running";
  if (status === "started") return "done";
  return "queued";
}
