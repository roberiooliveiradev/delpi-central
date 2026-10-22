import { parseGeneralRequestPayload } from "../features/general-request/domain/generalRequestPayload";
import { parseProcessIssuePayload } from "../features/process-issue/domain/processIssuePayload";
import type { RequestSummary } from "../types/requests";

/**
 * Título/assunto legível para listas (mine / work-queue).
 * Usa campos do payload já retornados pela API — sem fetch extra.
 */
export function requestListTitle(row: RequestSummary): string | null {
  const payload = row.payload;
  if (!payload || typeof payload !== "object") return null;

  switch (row.type_code) {
    case "general-request": {
      return parseGeneralRequestPayload(payload).title;
    }
    case "invoice-issuance": {
      const name = String(payload.party_name ?? "").trim();
      return name || null;
    }
    case "process-issue": {
      const view = parseProcessIssuePayload(payload);
      const parts = [view.issueLabel, view.productionOrder].filter(Boolean);
      return parts.length ? parts.join(" · ") : view.note;
    }
    default: {
      const title = String(payload.title ?? "").trim();
      if (title) return title;
      const description = String(payload.description ?? "").trim();
      return description || null;
    }
  }
}

export function requestListRequesterName(row: RequestSummary): string {
  return row.created_by_name?.trim() || "—";
}
