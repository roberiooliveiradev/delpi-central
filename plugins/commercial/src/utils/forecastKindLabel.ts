import type { LineOpForecastKind } from "../types/opForecast";

const KIND_LABELS: Record<LineOpForecastKind, string> = {
  estoque: "Coberto por estoque",
  sem_op: "Sem OP aberta",
  coberto: "Coberto por OP",
  parcial: "Cobertura parcial",
  sem_data: "OP sem data prevista",
};

export function forecastKindLabel(kind: LineOpForecastKind): string {
  return KIND_LABELS[kind] ?? kind;
}

export function forecastKindBadgeVariant(
  kind: LineOpForecastKind,
): "neutral" | "info" | "success" | "warning" | "danger" {
  if (kind === "estoque" || kind === "coberto") return "success";
  if (kind === "parcial" || kind === "sem_data") return "warning";
  if (kind === "sem_op") return "danger";
  return "neutral";
}
