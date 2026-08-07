import type {
  ProductionOrderLinkSummary,
  ProductionOrderRow,
} from "../types/productionExtras";

export const PRODUCTION_OTD_BASE_PATH = "/apps/dashboard-production/otd";

function asFiniteNumber(value: unknown): number | null {
  if (value == null || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/** Monta deep link para o detalhe OTD da OP no dashboard de produção. */
export function buildProductionOtdOrderPath(
  productionOrder: string,
  options?: { branch?: string | null; productType?: string | null },
): string | null {
  const op = String(productionOrder || "").trim();
  if (!op) return null;

  const base = `${PRODUCTION_OTD_BASE_PATH}/op/${encodeURIComponent(op)}`;
  const params = new URLSearchParams();
  const branch = String(options?.branch || "").trim();
  if (branch) params.set("branch", branch);

  const productType = String(options?.productType || "")
    .trim()
    .toUpperCase();
  if (productType === "PA" || productType === "PI") {
    params.set("product_type", productType);
  }

  const query = params.toString();
  return query ? `${base}?${query}` : base;
}

export function parseProductionLinkSummary(
  raw: ProductionOrderLinkSummary | Record<string, unknown> | null | undefined,
): ProductionOrderLinkSummary | null {
  if (!raw || typeof raw !== "object") return null;
  const row = raw as Record<string, unknown>;
  return {
    order_number:
      row.order_number != null ? String(row.order_number).trim() || null : null,
    link_field: row.link_field != null ? String(row.link_field).trim() || null : null,
    total_pi_orders: asFiniteNumber(row.total_pi_orders),
    on_time_ops: asFiniteNumber(row.on_time_ops),
    late_ops: asFiniteNumber(row.late_ops),
    open_ops: asFiniteNumber(row.open_ops),
  };
}

export function formatOtdStatusLabel(status: string | null | undefined): string {
  if (!status) return "—";
  if (status === "on_time") return "No prazo";
  if (status === "late") return "Atrasado";
  if (status === "open") return "Em aberto";
  return status;
}

export function otdStatusBadgeVariant(
  status: string | null | undefined,
): "success" | "danger" | "info" | "neutral" {
  if (status === "late") return "danger";
  if (status === "on_time") return "success";
  if (status === "open") return "info";
  return "neutral";
}

/** Dias previsto × real — negativo = finalização antes do previsto. */
export function formatOtdDaysDiff(days: number | null | undefined): string {
  if (days == null || !Number.isFinite(Number(days))) return "—";
  const n = Math.trunc(Number(days));
  return new Intl.NumberFormat("pt-BR", { signDisplay: "exceptZero" }).format(n);
}

export function linkedPiOrders(
  linked: ProductionOrderRow[] | null | undefined,
  limit = 5,
): ProductionOrderRow[] {
  const rows = (linked ?? []).filter((row) =>
    Boolean(String(row.production_order || "").trim()),
  );
  const pis = rows.filter((row) => {
    const type = String(row.product_type || "").trim().toUpperCase();
    return !type || type === "PI";
  });
  const source = pis.length > 0 ? pis : rows;
  return source.slice(0, Math.max(0, limit));
}
