import { copy } from "../content/copy";
import type { MachineLoadLocateJourney, MachineLoadLocateStop } from "../types";
import { hasExhaustedMachineLoadBalance, machineLoadStatusBadge } from "./machineLoadStatus";

/** C2_NUM = 6 primeiros dígitos da chave completa da OP (C2_OP / H8_OP, 11 posições). */
export const CONJUNTO_KEY_LENGTH = 6;

export function conjuntoKeyFromOrder(productionOrder: string | null | undefined): string | null {
  const code = (productionOrder || "").trim().toUpperCase();
  if (code.length < CONJUNTO_KEY_LENGTH) return null;
  return code.slice(0, CONJUNTO_KEY_LENGTH);
}

export function machineLoadLocateRowKey(
  stop: Pick<MachineLoadLocateStop, "work_center" | "production_order" | "operation_code">,
): string {
  // CT entra na chave: mesmo OP+operação pode aparecer em duas bancadas.
  return `${stop.work_center}::${stop.production_order}::${stop.operation_code}`;
}

export type LocateStopTone = "done" | "running" | "stopped" | "paused" | "unknown" | "queued";

export type LocateProgressStep = {
  tone: LocateStopTone;
  label: string;
};

/**
 * Resumo visual da jornada — mesma projeção da fila, vinda do cockpit:
 * produzindo / parada / pausada / não confirmada / já apontada / na fila.
 */
export function locateJourneyProgress(stops: MachineLoadLocateStop[]): LocateProgressStep[] {
  return stops.map((stop) => ({
    tone: locateStopStatusTone(stop),
    label: locateStopStatusLabel(stop),
  }));
}

export function locateJourneyTitle(journey: MachineLoadLocateJourney): string {
  // kind "op" = conjunto (C2_NUM, 6 dígitos); kind "pa" = produto acabado.
  if (journey.kind === "op") {
    return copy.machineLoad.locate.journeyConjunto(journey.key);
  }
  return copy.machineLoad.locate.journeyProduct(journey.key);
}

/** Label do estado da parada — execução do cockpit; saldo esgotado sem run = já apontada. */
export function locateStopStatusLabel(stop: MachineLoadLocateStop): string {
  switch (stop.execution_status) {
    case "producing":
      return machineLoadStatusBadge("in_progress").label;
    case "stopped":
      return machineLoadStatusBadge("stopped").label;
    case "paused":
      return machineLoadStatusBadge("paused").label;
    case "unknown":
      return machineLoadStatusBadge("unconfirmed").label;
    default:
      break;
  }
  if (hasExhaustedMachineLoadBalance(stop)) {
    return machineLoadStatusBadge("started").label;
  }
  return machineLoadStatusBadge("not_started").label;
}

export function locateStopStatusTone(stop: MachineLoadLocateStop): LocateStopTone {
  switch (stop.execution_status) {
    case "producing":
      return "running";
    case "stopped":
      return "stopped";
    case "paused":
      return "paused";
    case "unknown":
      return "unknown";
    default:
      break;
  }
  if (hasExhaustedMachineLoadBalance(stop)) return "done";
  return "queued";
}
