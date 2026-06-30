import { actionTypeLabel } from "../../constants/actionPlans";
import type { PlanAction } from "../../types/actionPlan";

export function formatEvidenceFileSize(bytes?: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function linkedActionLabel(action: PlanAction): string {
  const type = actionTypeLabel(action.action_type);
  const text = action.description.trim() || "Sem descrição";
  const snippet = text.length > 64 ? `${text.slice(0, 64)}…` : text;
  return `${type} · ${snippet}`;
}

export function linkedActionCell(
  actionId: string | null | undefined,
  actionById: Map<string, PlanAction>,
): string {
  if (!actionId) return "—";
  const action = actionById.get(actionId);
  return action ? linkedActionLabel(action) : actionId.slice(0, 8);
}

export function inferEvidenceTypeFromFile(file: File): string {
  const mime = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  if (mime.startsWith("image/")) return "image";
  if (mime === "application/pdf") return "pdf";
  if (
    mime.includes("spreadsheet")
    || mime.includes("excel")
    || name.endsWith(".xlsx")
    || name.endsWith(".xls")
  ) {
    return "spreadsheet";
  }
  if (mime.startsWith("text/") || name.endsWith(".txt") || name.endsWith(".csv")) {
    return "manual_text";
  }
  if (mime.includes("word") || name.endsWith(".doc") || name.endsWith(".docx")) {
    return "other";
  }
  return "other";
}

export function createPendingUploadId(): string {
  return `pending-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
