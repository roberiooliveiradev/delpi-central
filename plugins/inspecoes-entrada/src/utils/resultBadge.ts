export type ResultBadgeTone = "success" | "danger" | "warning" | "neutral";

export type ResultBadgeDescriptor = {
  label: string;
  tone: ResultBadgeTone;
};

export function resolveResultBadge(result: string): ResultBadgeDescriptor {
  const normalized = result.trim().toUpperCase();

  if (normalized === "APROVADA") {
    return { label: "APROVADA", tone: "success" };
  }

  if (normalized === "REJEITADA") {
    return { label: "REJEITADA", tone: "danger" };
  }

  if (!normalized) {
    return { label: "—", tone: "neutral" };
  }

  return { label: result.trim(), tone: "warning" };
}
