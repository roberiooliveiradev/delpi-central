/**
 * Contagem do badge «Meus pedidos» na topbar: linhas ready_to_invoice.
 */

export type KanbanStageCounts = {
  stages?: Array<{ id?: string; lineCount?: number | null }> | null;
};

/** lineCount da etapa ready_to_invoice; 0 se ausente. */
export function resolveReadyToInvoiceBadgeCount(
  counts: KanbanStageCounts | null | undefined,
): number {
  const stages = counts?.stages;
  if (!Array.isArray(stages)) return 0;
  const stage = stages.find((item) => (item?.id || "").trim() === "ready_to_invoice");
  const raw = stage?.lineCount;
  if (typeof raw !== "number" || !Number.isFinite(raw)) return 0;
  return Math.max(0, Math.trunc(raw));
}
