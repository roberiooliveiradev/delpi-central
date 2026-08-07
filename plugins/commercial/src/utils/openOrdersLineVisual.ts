import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { resolveOpVsPedidoPrazo } from "./dates";
import { formatQuantity } from "./format";
import { getLineOpForecast } from "./opAllocation";
import { getAllocatedStock } from "./stockAllocation";

export type CoverageTone = "neutral" | "success" | "warning" | "danger";

export function resolveLineCoverage(item: OpenOrdersTotvsItem): {
  allocated: number;
  saldo: number;
  ratio: number;
  percentLabel: string;
  quantityLabel: string;
  tone: CoverageTone;
} {
  const saldo = Math.max(0, item.saldo);
  const allocated = Math.max(0, getAllocatedStock(item));
  const ratio = saldo > 0 ? Math.min(1, allocated / saldo) : 1;
  let tone: CoverageTone = "neutral";
  if (saldo <= 0) tone = "neutral";
  else if (ratio >= 0.999) tone = "success";
  else if (ratio > 0) tone = "warning";
  else tone = "danger";

  return {
    allocated,
    saldo,
    ratio,
    percentLabel: `${Math.round(ratio * 100)}%`,
    quantityLabel: `${formatQuantity(allocated)} / ${formatQuantity(saldo)}`,
    tone,
  };
}

export function resolvePrevisaoPrazoBadge(item: OpenOrdersTotvsItem): {
  label: string;
  variant: "success" | "danger" | "neutral";
} | null {
  const previsao = getLineOpForecast(item);
  if (!previsao.opsUtilizadas.length) {
    if (previsao.previsaoLabel === "—" || !previsao.previsaoLabel) return null;
    return { label: "Sem OP", variant: "neutral" };
  }
  const prazo = resolveOpVsPedidoPrazo(previsao.previsaoData, item.data_entrega);
  if (prazo.status === "no_prazo") return { label: "No prazo", variant: "success" };
  if (prazo.status === "atrasado") return { label: "Atrasado", variant: "danger" };
  return { label: "Prazo", variant: "neutral" };
}
