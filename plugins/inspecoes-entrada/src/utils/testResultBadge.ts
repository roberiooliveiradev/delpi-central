import type { ResultBadgeDescriptor } from "./resultBadge";

export function resolveTestResultBadge(result: string, resultCode?: string): ResultBadgeDescriptor {
  const normalized = result.trim().toUpperCase();

  if (normalized === "APROVADO" || resultCode?.trim().toUpperCase() === "A") {
    return { label: "APROVADO", tone: "success" };
  }

  if (normalized === "REPROVADO" || resultCode?.trim().toUpperCase() === "R") {
    return { label: "REPROVADO", tone: "danger" };
  }

  if (!normalized) {
    return { label: "—", tone: "neutral" };
  }

  return { label: result.trim(), tone: "warning" };
}
