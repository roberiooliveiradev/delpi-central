import type { DeliveryMapOpProgress } from "./api";

/** Linha riscada só quando o conjunto (C2_NUM) atingiu 100% de progresso fabril. */
export function isDeliveryMapRowReported(
  progress: DeliveryMapOpProgress | undefined,
): boolean {
  return (progress?.percent ?? 0) >= 100;
}
