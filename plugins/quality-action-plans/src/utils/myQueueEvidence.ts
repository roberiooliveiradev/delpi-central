import type { MyQueueItem } from "../types/myQueue";

export function queueItemMissingRequiredEvidence(
  item: Pick<MyQueueItem, "evidence_required" | "evidence_count">,
): boolean {
  return Boolean(item.evidence_required) && (item.evidence_count ?? 0) < 1;
}

export function queueItemEvidenceLabel(
  item: Pick<MyQueueItem, "evidence_required" | "evidence_count">,
): string {
  if (!item.evidence_required) {
    return "Opcional";
  }
  if ((item.evidence_count ?? 0) > 0) {
    const count = item.evidence_count ?? 0;
    return count === 1 ? "1 anexo" : `${count} anexos`;
  }
  return "Pendente";
}
