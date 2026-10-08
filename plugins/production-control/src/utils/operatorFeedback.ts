import { copy } from "../content/copy";
import type { MachineLoadOperation, PcpOperatorFeedback } from "../types";

/** Codigos oficiais do dominio Operator Feedback (espelho do enum da C1). */
export const OPERATOR_FEEDBACK_TYPE_CANNOT_PRODUCE = "cannot_produce";
export const OPERATOR_FEEDBACK_REASON_MISSING_MATERIAL = "missing_material";

const TYPE_LABELS: Record<string, string> = {
  [OPERATOR_FEEDBACK_TYPE_CANNOT_PRODUCE]: copy.machineLoad.feedback.typeCannotProduce,
};

const REASON_LABELS: Record<string, string> = {
  [OPERATOR_FEEDBACK_REASON_MISSING_MATERIAL]: copy.machineLoad.feedback.reasonMissingMaterial,
};

/** Mesma normalizacao do backend: C2_OP pode vir "030" no TOTVS e "30" na fila. */
export function normalizeOperationCode(code: string | null | undefined): string {
  const cleaned = (code ?? "").trim().replace(/^0+/, "");
  return cleaned || "0";
}

/** Identidade funcional do feedback: filial + OP + operacao.
 *  reportedWorkCenter NAO participa — a OP pode ter sido transferida. */
export function operatorFeedbackKey(
  productionOrder: string | null | undefined,
  operationCode: string | null | undefined,
): string {
  return `${(productionOrder ?? "").trim().toUpperCase()}::${normalizeOperationCode(operationCode)}`;
}

export function feedbackKeyForOperation(
  operation: Pick<MachineLoadOperation, "production_order" | "operation_code">,
): string {
  return operatorFeedbackKey(operation.production_order, operation.operation_code);
}

/** 1 GET por filial → mapa local OP+operacao → feedback ativo (sem N+1). */
export function indexFeedbackByOperation(
  items: readonly PcpOperatorFeedback[],
): Map<string, PcpOperatorFeedback> {
  const map = new Map<string, PcpOperatorFeedback>();
  for (const item of items) {
    map.set(operatorFeedbackKey(item.productionOrder, item.operationCode), item);
  }
  return map;
}

export function feedbackForOperation(
  map: ReadonlyMap<string, PcpOperatorFeedback>,
  operation: Pick<MachineLoadOperation, "production_order" | "operation_code">,
): PcpOperatorFeedback | null {
  return map.get(feedbackKeyForOperation(operation)) ?? null;
}

/** Filtro "Com impedimento": operacoes visiveis que possuem feedback ativo. */
export function filterOperationsWithFeedback(
  rows: readonly MachineLoadOperation[],
  map: ReadonlyMap<string, PcpOperatorFeedback>,
): MachineLoadOperation[] {
  return rows.filter((row) => map.has(feedbackKeyForOperation(row)));
}

export function countOperationsWithFeedback(
  rows: readonly MachineLoadOperation[],
  map: ReadonlyMap<string, PcpOperatorFeedback>,
): number {
  return filterOperationsWithFeedback(rows, map).length;
}

export function feedbackStatusLabel(status: string): string {
  if (status === "acknowledged") return copy.machineLoad.feedback.statusAcknowledged;
  if (status === "resolved") return copy.machineLoad.feedback.statusResolved;
  return copy.machineLoad.feedback.statusOpen;
}

export function feedbackTypeLabel(code: string): string {
  return TYPE_LABELS[code] ?? code;
}

export function feedbackReasonLabel(code: string): string {
  return REASON_LABELS[code] ?? code;
}

/** Tom visual do indicador: open pede mais atencao que a tratativa em curso. */
export function feedbackBadgeTone(status: string): "attention" | "progress" | null {
  if (status === "open") return "attention";
  if (status === "acknowledged") return "progress";
  return null;
}

const MATERIAL_STATUS_LABELS: Record<string, string> = {
  pending: copy.machineLoad.feedback.materialPending,
  picked: copy.machineLoad.feedback.materialPicked,
  delivered: copy.machineLoad.feedback.materialDelivered,
};

/** Status do material na fila urgente do Alimentador (C5). */
export function feedbackMaterialStatusLabel(status: string): string {
  return MATERIAL_STATUS_LABELS[status] ?? copy.machineLoad.feedback.materialPending;
}

/** Materiais ainda não entregues — warning ao resolver, nunca bloqueio. */
export function hasUndeliveredMaterials(
  item: Pick<PcpOperatorFeedback, "materials">,
): boolean {
  return (item.materials ?? []).some(
    (material) => material.status !== "delivered",
  );
}

/** Localiza a operacao na fila atual da filial (qualquer CT) — serve ao
 *  "Ver na fila" e ao marcador "Fora da fila atual". */
export function findOperationInQueue(
  operations: readonly MachineLoadOperation[],
  feedback: Pick<PcpOperatorFeedback, "productionOrder" | "operationCode">,
): MachineLoadOperation | null {
  const key = operatorFeedbackKey(feedback.productionOrder, feedback.operationCode);
  return (
    operations.find(
      (operation) => feedbackKeyForOperation(operation) === key,
    ) ?? null
  );
}
